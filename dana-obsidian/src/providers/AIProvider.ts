export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AIProvider {
  name: string;
  generate(systemPrompt: string, messages: ChatMessage[], signal: AbortSignal): AsyncGenerator<string>;
  isAvailable(): Promise<boolean>;
}
