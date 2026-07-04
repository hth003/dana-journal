export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

/** Final state of a completed stream. */
export interface GenerationEnd {
  /** The model hit its token cap — the response is cut off, not finished. */
  truncated: boolean;
}

export interface AIProvider {
  name: string;
  /**
   * Yields text chunks; the generator's RETURN value reports truncation.
   * Iterate with a manual `next()` loop — `for await` discards return values.
   */
  generate(
    systemPrompt: string,
    messages: ChatMessage[],
    signal: AbortSignal
  ): AsyncGenerator<string, GenerationEnd>;
  isAvailable(): Promise<boolean>;
}
