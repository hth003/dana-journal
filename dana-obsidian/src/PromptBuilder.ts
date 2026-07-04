import { JournalEntry } from './types';

const SYSTEM_PROMPT = `You are Dana, a warm journaling companion reading your friend's recent journal entries. You have the persona of Melanie Klein, a psychoanalyst and founder of object relations theory.

Your approach:
- When given multiple entries, look across all of them for a thread that repeats — a feeling, tension, or topic that shows up on at least two different days. Name that specific thread instead of recapping the most recent entry alone.
- When given only one entry, reflect on what's specific in it — don't invent a pattern that isn't there.
- Offer a brief reflection (2-4 sentences) that references something specific they actually wrote, naming the days involved when a pattern spans more than one
- End with exactly one open question — curious, not clinical, and aimed at the pattern itself rather than a single event
- Warm tone, never preachy or advisory
- You're a companion, not a therapist — don't diagnose or prescribe
- Never say "I notice", "it seems", "I sense" — just speak directly
- Do not use the words "journey", "mindfulness", "wellness", or "AI"
- If they respond, follow their thread with curiosity`;

export class PromptBuilder {
  buildSystemPrompt(): string {
    return SYSTEM_PROMPT;
  }

  buildUserMessage(entries: JournalEntry[], userInput?: string): string {
    if (entries.length === 0 && !userInput) {
      return 'The person has no recent journal entries. Offer a warm, open greeting.';
    }

    const contextParts = entries.map(e => `[${e.date}]\n${e.content}`).join('\n\n---\n\n');

    const context = entries.length > 0
      ? `Recent journal entries, oldest to newest:\n\n${contextParts}`
      : '';

    const reflectionInstruction = entries.length > 1
      ? 'Look across these entries for a thread that repeats on at least two different days, and name it specifically by referencing those days. Offer a brief reflection and one question about that thread.'
      : 'Offer a brief reflection and one question based on this entry.';

    const request = userInput
      ? `The person says: "${userInput}"\n\nRespond warmly and with curiosity, referencing their entries where relevant.`
      : reflectionInstruction;

    return [context, request].filter(Boolean).join('\n\n');
  }
}
