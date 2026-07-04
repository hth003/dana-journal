export interface DanaSettings {
  journalFolder: string;
  maxContextEntries: number;
  ollamaHost: string;
  ollamaModel: string;
  openaiKeyEncrypted: string;
  openaiKeyEncryptionAvailable: boolean;
  preferredProvider: 'ollama' | 'openai';
  onboarded: boolean;
}

export const DEFAULT_SETTINGS: DanaSettings = {
  journalFolder: '',
  maxContextEntries: 7,
  ollamaHost: 'http://localhost:11434',
  ollamaModel: 'llama3.2',
  openaiKeyEncrypted: '',
  openaiKeyEncryptionAvailable: false,
  preferredProvider: 'ollama',
  onboarded: false,
};

export enum DanaState {
  SETUP = 'setup',
  IDLE = 'idle',
  LOADING = 'loading',
  STREAMING = 'streaming',
  DONE = 'done',
  CONVERSATION = 'conversation',
  ERROR_NO_AI = 'error_no_ai',
  ERROR_TIMEOUT = 'error_timeout',
  ERROR_NO_NOTES = 'error_no_notes',
  EMPTY_NOTES = 'empty_notes',
}

/**
 * What journal content grounds a reflection:
 *   entry — ONLY the currently open journal note
 *   week  — the last maxContextEntries entries, sorted by date
 */
export type ReflectionMode = 'entry' | 'week';

export interface ConversationMessage {
  role: 'dana' | 'user';
  content: string;
  timestamp: number;
  /** Generation was cut short (token cap or idle timeout) — render a marker. */
  truncated?: boolean;
}

/**
 * One conversation. Context files are pinned by PATH at start; their content
 * is re-read every turn so Dana quotes what the note says NOW, with the
 * start-of-conversation snapshot as fallback if a file disappears.
 */
export interface ConversationSession {
  mode: ReflectionMode;
  contextPaths: string[];
  messages: ConversationMessage[];
}

export interface JournalEntry {
  date: string;
  content: string;
  path: string;
}
