import { PromptBuilder } from '../src/PromptBuilder';
import { JournalEntry } from '../src/types';

const builder = new PromptBuilder();

function makeEntry(date: string, content: string): JournalEntry {
  return { date, content, path: `Daily Notes/${date}.md` };
}

describe('PromptBuilder.buildSystemPrompt', () => {
  it('returns a non-empty string', () => {
    const prompt = builder.buildSystemPrompt();
    expect(prompt.length).toBeGreaterThan(0);
  });

  it('does not promote "AI-powered" language in user-facing framing', () => {
    const prompt = builder.buildSystemPrompt().toLowerCase();
    // The instructions may mention banned words as examples to avoid,
    // but should not contain marketing framing Dana would output.
    expect(prompt).not.toContain('ai-powered journaling');
    expect(prompt).not.toContain('leverage ai');
    expect(prompt).not.toContain('unlock the power');
  });

  it('establishes Dana as a companion not a therapist', () => {
    const prompt = builder.buildSystemPrompt().toLowerCase();
    expect(prompt).toContain('companion');
    expect(prompt).toContain('not a therapist');
  });
});

describe('PromptBuilder.buildUserMessage', () => {
  it('handles empty entries gracefully', () => {
    const msg = builder.buildUserMessage([]);
    expect(msg.length).toBeGreaterThan(0);
  });

  it('includes entry dates in context', () => {
    const entries = [makeEntry('2026-04-18', 'Felt stressed about the project deadline.')];
    const msg = builder.buildUserMessage(entries);
    expect(msg).toContain('2026-04-18');
    expect(msg).toContain('stressed');
  });

  it('includes userInput when provided', () => {
    const entries = [makeEntry('2026-04-18', 'Felt peaceful walking in the park.')];
    const msg = builder.buildUserMessage(entries, "I need to process something.");
    expect(msg).toContain('I need to process something');
  });

  it('includes all entries separated by dividers', () => {
    const entries = [
      makeEntry('2026-04-18', 'Today was tough. Work was overwhelming.'),
      makeEntry('2026-04-17', 'Yesterday I felt tired but managed.'),
    ];
    const msg = builder.buildUserMessage(entries);
    expect(msg).toContain('2026-04-18');
    expect(msg).toContain('2026-04-17');
    expect(msg).toContain('---');
  });

  it('does not mention "AI" or "wellness" in user message', () => {
    const entries = [makeEntry('2026-04-18', 'Had a productive day.')];
    const msg = builder.buildUserMessage(entries).toLowerCase();
    expect(msg).not.toContain('ai-powered');
    expect(msg).not.toContain('wellness');
  });
});
