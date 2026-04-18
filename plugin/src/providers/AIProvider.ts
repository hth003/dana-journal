export interface AIProvider {
  name: string;
  generate(systemPrompt: string, userMessage: string, signal: AbortSignal): AsyncGenerator<string>;
  isAvailable(): Promise<boolean>;
}
