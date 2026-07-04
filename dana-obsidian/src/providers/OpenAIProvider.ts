import { AIProvider, ChatMessage, GenerationEnd } from './AIProvider';

export class OpenAIProvider implements AIProvider {
  name = 'OpenAI';

  constructor(private apiKey: string) {}

  async isAvailable(): Promise<boolean> {
    return this.apiKey.trim().length > 0;
  }

  async *generate(systemPrompt: string, messages: ChatMessage[], signal: AbortSignal): AsyncGenerator<string, GenerationEnd> {
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
        max_tokens: 1024,
      }),
      signal,
    });

    if (!resp.ok) {
      throw new Error(`OpenAI ${resp.status}: ${await resp.text()}`);
    }

    const reader = resp.body!.getReader();
    const decoder = new TextDecoder();
    // SSE lines can straddle network reads — carry the unterminated tail over.
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
          if (!line.startsWith('data: ') || line === 'data: [DONE]') continue;
          try {
            const data = JSON.parse(line.slice(6));
            const chunk = data.choices?.[0]?.delta?.content;
            if (chunk) yield chunk;
            if (data.choices?.[0]?.finish_reason === 'length') {
              truncated = true;
            }
          } catch {
            // genuinely malformed SSE line — skip
          }
        }
      }
      return { truncated };
    } finally {
      reader.releaseLock();
    }
  }
}
