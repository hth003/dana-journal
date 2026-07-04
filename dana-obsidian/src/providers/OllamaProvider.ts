import { AIProvider, ChatMessage } from './AIProvider';

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

  async *generate(systemPrompt: string, messages: ChatMessage[], signal: AbortSignal): AsyncGenerator<string> {
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
      }),
      signal,
    });

    if (!resp.ok) {
      throw new Error(`Ollama ${resp.status}: ${await resp.text()}`);
    }

    const reader = resp.body!.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value, { stream: true });
        for (const line of text.split('\n')) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);
            const chunk = data.message?.content;
            if (chunk) yield chunk;
            if (data.done) return;
          } catch {
            // partial JSON chunk — skip
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }
}
