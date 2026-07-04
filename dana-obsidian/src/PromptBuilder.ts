import { JournalEntry } from './types';

const SYSTEM_PROMPT = `You are Dana, a warm journaling companion reading your friend's recent journal entries. You have the persona of Melanie Klein, a psychoanalyst and founder of object relations theory.

Your approach:
- Offer a brief reflection (2-4 sentences) that references something specific they actually wrote
- End with exactly one open question — curious, not clinical
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
      ? `Recent journal entries:\n\n${contextParts}`
      : '';

    const request = userInput
      ? `The person says: "${userInput}"\n\nRespond warmly and with curiosity, referencing their entries where relevant.`
      : 'Offer a brief reflection and one question based on these entries.';

    return [context, request].filter(Boolean).join('\n\n');
  }
}
