import { AIProvider, ChatMessage, GenerationEnd } from './AIProvider';

export class OllamaProvider implements AIProvider {
  name = 'Ollama';

  constructor(private host: string, private model: string) {}

  async isAvailable(): Promise<boolean> {
    try {
      const resp = await fetch(`${this.host}/api/tags`, {
        signal: AbortSignal.timeout(3000),
      });
      return resp.ok;
    } catch {
      return false;
    }
  }

  async *generate(systemPrompt: string, messages: ChatMessage[], signal: AbortSignal): AsyncGenerator<string, GenerationEnd> {
    const resp = await fetch(`${this.host}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: this.model,
        messages: [
          { role: 'system', content: systemPrompt },
          ...messages,
        ],
        stream: true,
        options: { num_predict: 1024 },
      }),
      signal,
    });

    if (!resp.ok) {
      throw new Error(`Ollama ${resp.status}: ${await resp.text()}`);
    }

    const reader = resp.body!.getReader();
    const decoder = new TextDecoder();
    // NDJSON objects can straddle network reads — carry the unterminated tail
    // over to the next read instead of trying (and failing) to parse halves.
    let buffer = '';
    let truncated = false;

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);
            const chunk = data.message?.content;
            if (chunk) yield chunk;
            if (data.done) {
              truncated = data.done_reason === 'length';
              return { truncated };
            }
          } catch {
            // genuinely malformed line — skip
          }
        }
      }
      // flush a final unterminated line (server closed without trailing \n)
      if (buffer.trim()) {
        try {
          const data = JSON.parse(buffer);
          const chunk = data.message?.content;
          if (chunk) yield chunk;
          truncated = data.done === true && data.done_reason === 'length';
        } catch {
          // incomplete tail — nothing usable
        }
      }
      return { truncated };
    } finally {
      reader.releaseLock();
    }
  }
}
