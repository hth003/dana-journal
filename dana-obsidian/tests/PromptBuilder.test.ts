import { PromptBuilder, INSIGHTS_LABEL } from '../src/PromptBuilder';
import { JournalEntry, ConversationMessage } from '../src/types';

const builder = new PromptBuilder();

function entry(date: string, content: string, path = `Daily Notes/${date}.md`): JournalEntry {
  return { date, content, path };
}

const BANNED = ['journey', 'mindfulness', 'wellness', 'robust', 'comprehensive', 'holistic'];

describe('PromptBuilder.buildSystemPrompt', () => {
  it('entry mode scopes Dana to the single provided note', () => {
    const prompt = builder.buildSystemPrompt('entry', [entry('2026-07-04', 'today I felt stuck')]);

    expect(prompt).toContain('exactly ONE journal entry');
    expect(prompt).toContain('today I felt stuck');
    expect(prompt).not.toContain('at least two different days');
  });

  it('week mode with multiple entries asks for a cross-day thread', () => {
    const prompt = builder.buildSystemPrompt('week', [
      entry('2026-07-03', 'deadline stress again'),
      entry('2026-07-04', 'the deadline is close'),
    ]);

    expect(prompt).toContain('at least two different days');
    expect(prompt).toContain('deadline stress again');
    expect(prompt).toContain('the deadline is close');
  });

  it('week mode with one entry falls back to single-entry framing (no invented patterns)', () => {
    const prompt = builder.buildSystemPrompt('week', [entry('2026-07-04', 'only entry')]);

    expect(prompt).toContain("don't invent a pattern");
    expect(prompt).not.toContain('at least two different days');
  });

  it('embeds entries oldest-to-newest with their dates', () => {
    const prompt = builder.buildSystemPrompt('week', [
      entry('2026-07-01', 'first'),
      entry('2026-07-04', 'last'),
    ]);

    expect(prompt.indexOf('[2026-07-01]')).toBeLessThan(prompt.indexOf('[2026-07-04]'));
  });

  it('establishes Dana as a companion not a therapist', () => {
    const prompt = builder.buildSystemPrompt('entry', [entry('2026-07-04', 'x')]).toLowerCase();
    expect(prompt).toContain('companion');
    expect(prompt).toContain('not a therapist');
  });

  it('never contains banned words outside the explicit prohibition line', () => {
    for (const mode of ['entry', 'week'] as const) {
      const prompt = builder
        .buildSystemPrompt(mode, [entry('2026-07-04', 'plain content')])
        .toLowerCase()
        .split('\n')
        .filter(line => !line.includes('do not use the words'))
        .join('\n');
      for (const word of BANNED) {
        expect(prompt).not.toContain(word);
      }
    }
  });
});

describe('PromptBuilder.buildFirstTurnInstruction', () => {
  it('requests the byte-exact ritual label in both modes', () => {
    expect(builder.buildFirstTurnInstruction('entry')).toContain(INSIGHTS_LABEL);
    expect(builder.buildFirstTurnInstruction('week')).toContain(INSIGHTS_LABEL);
    expect(INSIGHTS_LABEL).toBe('**Worth noticing:**');
  });

  it('requests exactly one closing question in italics', () => {
    const instruction = builder.buildFirstTurnInstruction('entry');
    expect(instruction).toContain('exactly one open question');
    expect(instruction).toContain('italics');
  });
});

describe('PromptBuilder.buildTurnMessages', () => {
  const history: ConversationMessage[] = [
    { role: 'user', content: 'first words', timestamp: 1 },
    { role: 'dana', content: 'a reflection', timestamp: 2 },
  ];

  it('first turn without input sends only the structured instruction', () => {
    const messages = builder.buildTurnMessages('entry', []);

    expect(messages).toHaveLength(1);
    expect(messages[0].role).toBe('user');
    expect(messages[0].content).toContain(INSIGHTS_LABEL);
  });

  it('first turn with user input includes their words alongside the instruction', () => {
    const messages = builder.buildTurnMessages('week', [], 'I feel scattered');

    expect(messages).toHaveLength(1);
    expect(messages[0].content).toContain(INSIGHTS_LABEL);
    expect(messages[0].content).toContain('I feel scattered');
  });

  it('later turns send clean history + the new input, WITHOUT the structure instruction', () => {
    const messages = builder.buildTurnMessages('entry', history, 'tell me more');

    expect(messages).toEqual([
      { role: 'user', content: 'first words' },
      { role: 'assistant', content: 'a reflection' },
      { role: 'user', content: 'tell me more' },
    ]);
    expect(JSON.stringify(messages)).not.toContain('Worth noticing');
  });

  it('later turns without input (retry) end on the prior user message', () => {
    const messages = builder.buildTurnMessages('entry', [history[0]]);

    expect(messages).toEqual([{ role: 'user', content: 'first words' }]);
  });
});

describe('journal context on every turn (regression: Dana forgot what she read)', () => {
  it('system prompt carries entry content regardless of turn number', () => {
    // Turn 2+: history is non-empty, but context lives in the system prompt,
    // which DanaPanel rebuilds every turn from re-read entries.
    const prompt = builder.buildSystemPrompt('entry', [entry('2026-07-04', 'the apartment search drags on')]);
    const turn2 = builder.buildTurnMessages('entry', [
      { role: 'dana', content: 'reflection', timestamp: 1 },
    ], 'why do I avoid it?');

    expect(prompt).toContain('the apartment search drags on');
    expect(turn2[turn2.length - 1].content).toBe('why do I avoid it?');
  });
});
