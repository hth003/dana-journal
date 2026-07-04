import { AIProvider, ChatMessage } from './AIProvider';

export class OpenAIProvider implements AIProvider {
  name = 'OpenAI';

  constructor(private apiKey: string) {}

  async isAvailable(): Promise<boolean> {
    return this.apiKey.trim().length > 0;
  }

  async *generate(systemPrompt: string, messages: ChatMessage[], signal: AbortSignal): AsyncGenerator<string> {
    const resp = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages: [
          { role: 'system', content: systemPrompt },
          ...messages,
        ],
        stream: true,
        max_tokens: 600,
      }),
      signal,
    });

    if (!resp.ok) {
      throw new Error(`OpenAI ${resp.status}: ${await resp.text()}`);
    }

    const reader = resp.body!.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value, { stream: true });
        for (const line of text.split('\n')) {
          if (!line.startsWith('data: ') || line === 'data: [DONE]') continue;
          try {
            const data = JSON.parse(line.slice(6));
            const chunk = data.choices?.[0]?.delta?.content;
            if (chunk) yield chunk;
          } catch {
            // skip malformed SSE line
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }
}
