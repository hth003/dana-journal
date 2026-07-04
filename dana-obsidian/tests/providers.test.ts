import { OllamaProvider } from '../src/providers/OllamaProvider';
import { OpenAIProvider } from '../src/providers/OpenAIProvider';
import type { GenerationEnd } from '../src/providers/AIProvider';

// Build a fetch mock whose body streams the given string chunks — chunk
// boundaries are the whole point of these tests.
function mockFetchStream(chunks: string[], ok = true, status = 200) {
  const encoder = new TextEncoder();
  let i = 0;
  return jest.fn().mockResolvedValue({
    ok,
    status,
    text: async () => 'error body',
    body: {
      getReader: () => ({
        read: async () =>
          i < chunks.length
            ? { done: false, value: encoder.encode(chunks[i++]) }
            : { done: true, value: undefined },
        releaseLock: () => {},
      }),
    },
  });
}

async function collect(gen: AsyncGenerator<string, GenerationEnd>): Promise<{ text: string; end: GenerationEnd }> {
  let text = '';
  while (true) {
    const { done, value } = await gen.next();
    if (done) return { text, end: value };
    text += value;
  }
}

const signal = new AbortController().signal;

describe('OllamaProvider streaming', () => {
  it('CRITICAL regression guard: reassembles an NDJSON object split across two reads', async () => {
    const line1 = JSON.stringify({ message: { content: 'Hello ' } });
    const line2 = JSON.stringify({ message: { content: 'world' } });
    const line3 = JSON.stringify({ done: true, done_reason: 'stop' });
    // Split line2 mid-object across two network reads
    const mid = Math.floor(line2.length / 2);
    global.fetch = mockFetchStream([
      line1 + '\n' + line2.slice(0, mid),
      line2.slice(mid) + '\n' + line3 + '\n',
    ]) as any;

    const provider = new OllamaProvider('http://localhost:11434', 'llama3.2');
    const { text, end } = await collect(provider.generate('sys', [], signal));

    expect(text).toBe('Hello world');
    expect(end.truncated).toBe(false);
  });

  it('reports truncation when done_reason is length', async () => {
    global.fetch = mockFetchStream([
      JSON.stringify({ message: { content: 'cut off mid' } }) + '\n',
      JSON.stringify({ done: true, done_reason: 'length' }) + '\n',
    ]) as any;

    const provider = new OllamaProvider('http://localhost:11434', 'llama3.2');
    const { text, end } = await collect(provider.generate('sys', [], signal));

    expect(text).toBe('cut off mid');
    expect(end.truncated).toBe(true);
  });

  it('throws a named error on non-OK responses', async () => {
    global.fetch = mockFetchStream([], false, 500) as any;

    const provider = new OllamaProvider('http://localhost:11434', 'llama3.2');
    await expect(collect(provider.generate('sys', [], signal))).rejects.toThrow('Ollama 500');
  });
});

describe('OpenAIProvider streaming', () => {
  it('reassembles an SSE line split across two reads', async () => {
    const sse = (obj: unknown) => `data: ${JSON.stringify(obj)}\n`;
    const line = sse({ choices: [{ delta: { content: 'together' } }] });
    const mid = Math.floor(line.length / 2);
    global.fetch = mockFetchStream([
      sse({ choices: [{ delta: { content: 'held ' } }] }) + line.slice(0, mid),
      line.slice(mid) + 'data: [DONE]\n',
    ]) as any;

    const provider = new OpenAIProvider('sk-test');
    const { text, end } = await collect(provider.generate('sys', [], signal));

    expect(text).toBe('held together');
    expect(end.truncated).toBe(false);
  });

  it('reports truncation when finish_reason is length', async () => {
    const sse = (obj: unknown) => `data: ${JSON.stringify(obj)}\n`;
    global.fetch = mockFetchStream([
      sse({ choices: [{ delta: { content: 'capped' } }] }) +
      sse({ choices: [{ delta: {}, finish_reason: 'length' }] }) +
      'data: [DONE]\n',
    ]) as any;

    const provider = new OpenAIProvider('sk-test');
    const { text, end } = await collect(provider.generate('sys', [], signal));

    expect(text).toBe('capped');
    expect(end.truncated).toBe(true);
  });

  it('requests a 1024-token budget (structured responses need room)', async () => {
    const fetchMock = mockFetchStream(['data: [DONE]\n']);
    global.fetch = fetchMock as any;

    const provider = new OpenAIProvider('sk-test');
    await collect(provider.generate('sys', [], signal));

    const body = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(body.max_tokens).toBe(1024);
  });
});
