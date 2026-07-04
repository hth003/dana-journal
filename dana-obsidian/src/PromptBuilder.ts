import { JournalEntry, ConversationMessage, ReflectionMode } from './types';
import type { ChatMessage } from './providers/AIProvider';

/**
 * Prompt assembly per turn:
 *
 *   system prompt = persona + mode rules + CURRENT journal context
 *                   (rebuilt every turn from re-read entries, so Dana
 *                    quotes what the note says now)
 *   messages      = clean user/dana history + the new user input
 *   turn 1 only   = structured-reflection instruction (the ritual shape)
 */

const PERSONA = `You are Dana, a warm journaling companion reading your friend's journal. You have the persona of Melanie Klein, a psychoanalyst and founder of object relations theory.

Your approach:
- Reference something specific they actually wrote — quote their own words back when it helps
- Warm tone, never preachy or advisory
- You're a companion, not a therapist — don't diagnose or prescribe
- Never say "I notice", "it seems", "I sense" — just speak directly
- Do not use the words "journey", "mindfulness", "wellness", or "AI"
- If they respond, follow their thread with curiosity`;

const ENTRY_RULES = `You are reading exactly ONE journal entry — the note your friend has open right now. Ground everything in this entry alone. Do not reference, imply, or invent anything that is not written in it.`;

const WEEK_RULES = `You are reading several days of journal entries. Look across all of them for a thread that repeats — a feeling, tension, or topic that shows up on at least two different days. Name that specific thread and the days involved instead of recapping the most recent entry alone.`;

const WEEK_SINGLE_RULES = `You have only one journal entry available. Reflect on what's specific in it — don't invent a pattern that isn't there.`;

// Fixed ritual label — byte-identical every reflection. Tests assert this
// exact string; the UI relies on it to give first responses a scannable shape.
export const INSIGHTS_LABEL = '**Worth noticing:**';

export class PromptBuilder {
  buildSystemPrompt(mode: ReflectionMode, entries: JournalEntry[]): string {
    const rules =
      mode === 'entry' ? ENTRY_RULES
      : entries.length > 1 ? WEEK_RULES
      : WEEK_SINGLE_RULES;

    const context = entries.length > 0
      ? `Journal ${entries.length > 1 ? 'entries, oldest to newest' : 'entry'}:\n\n` +
        entries.map(e => `[${e.date}]\n${e.content}`).join('\n\n---\n\n')
      : 'There are no journal entries available.';

    return [PERSONA, rules, context].join('\n\n');
  }

  /**
   * The structured first response — same shape every time, like a well-worn
   * notebook: short reflection, "Worth noticing" bullets, one question.
   */
  buildFirstTurnInstruction(mode: ReflectionMode): string {
    const grounding = mode === 'entry'
      ? 'Reflect on this entry.'
      : 'Reflect across these entries, naming a thread that repeats and the days involved (or, with a single entry, what stands out in it).';

    return `${grounding} Structure your response exactly like this, in markdown:

1. Open with 2-3 sentences of reflection that reference something specific they wrote.
2. Then a section starting with the exact label ${INSIGHTS_LABEL} followed by 2-3 bullet points: one about their feelings or situation, one about outside influences, people, or relationships, and one about something they mentioned but the first two bullets didn't address.
3. End with exactly one open question, in italics, on its own line — curious, not clinical.

Do not add any other headings or sections.`;
  }

  /**
   * Pure per-turn API payload assembly (extracted so tests can cover it
   * without touching Obsidian). First turn sends the structured instruction;
   * later turns send clean conversation history plus the new user input.
   */
  buildTurnMessages(
    mode: ReflectionMode,
    history: ConversationMessage[],
    userInput?: string
  ): ChatMessage[] {
    if (history.length === 0) {
      const instruction = this.buildFirstTurnInstruction(mode);
      const content = userInput
        ? `${instruction}\n\nThey begin by saying: "${userInput}"`
        : instruction;
      return [{ role: 'user', content }];
    }

    const messages: ChatMessage[] = history.map(m => ({
      role: (m.role === 'dana' ? 'assistant' : 'user') as 'user' | 'assistant',
      content: m.content,
    }));
    if (userInput) {
      messages.push({ role: 'user', content: userInput });
    }
    return messages;
  }
}
