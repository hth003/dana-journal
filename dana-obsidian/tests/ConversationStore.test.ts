import { ConversationStore } from '../src/ConversationStore';
import { ConversationSession } from '../src/types';

// serialize/parse/localToday are pure — test without Obsidian
const store = new ConversationStore(null as any);

const structuredResponse = [
  'You wrote about the deadline again, and this time it came with the apartment search.',
  '',
  '**Worth noticing:**',
  '- The deadline shows up next to rest, never work',
  '- Both entries mention your sister',
  '',
  '*What would it mean to let one of these wait?*',
].join('\n');

function session(overrides: Partial<ConversationSession> = {}): ConversationSession {
  return {
    mode: 'entry',
    contextPaths: ['Daily Notes/2026-07-04.md'],
    messages: [
      { role: 'dana', content: structuredResponse, timestamp: 0 },
      { role: 'user', content: 'Honestly exhausting.', timestamp: 0 },
    ],
    ...overrides,
  };
}

describe('ConversationStore v2 round-trip', () => {
  it('preserves multi-paragraph structured responses (regression: v1 ate everything after the first blank line)', () => {
    const text = store.serialize('2026-07-04', [session()]);
    const parsed = store.parse(text);

    expect(parsed).toHaveLength(1);
    expect(parsed[0].messages[0].content).toBe(structuredResponse);
    expect(parsed[0].messages[1].content).toBe('Honestly exhausting.');
  });

  it('preserves mode and contextPaths', () => {
    const text = store.serialize('2026-07-04', [session()]);
    const parsed = store.parse(text);

    expect(parsed[0].mode).toBe('entry');
    expect(parsed[0].contextPaths).toEqual(['Daily Notes/2026-07-04.md']);
  });

  it('preserves the truncated flag', () => {
    const s = session();
    s.messages[0].truncated = true;
    const parsed = store.parse(store.serialize('2026-07-04', [s]));

    expect(parsed[0].messages[0].truncated).toBe(true);
    expect(parsed[0].messages[1].truncated).toBeUndefined();
  });

  it('holds multiple sessions in one day file', () => {
    const s1 = session();
    const s2 = session({ mode: 'week', contextPaths: ['a.md', 'b.md'] });
    const parsed = store.parse(store.serialize('2026-07-04', [s1, s2]));

    expect(parsed).toHaveLength(2);
    expect(parsed[1].mode).toBe('week');
    expect(parsed[1].contextPaths).toEqual(['a.md', 'b.md']);
  });

  it('round-trips a user message containing a literal delimiter line without splitting', () => {
    const hostile = 'look what I found:\n<!-- dana:msg role=user -->\nwild, right?';
    const s = session();
    s.messages.push({ role: 'user', content: hostile, timestamp: 0 });
    const parsed = store.parse(store.serialize('2026-07-04', [s]));

    expect(parsed[0].messages).toHaveLength(3);
    expect(parsed[0].messages[2].content).toBe(hostile);
  });

  it('parses legacy v1 files as a single week session', () => {
    const v1 = '**Dana:** I noticed you wrote about stress. What does it feel like?\n\n**Me:** Exhausting honestly.';
    const parsed = store.parse(v1);

    expect(parsed).toHaveLength(1);
    expect(parsed[0].mode).toBe('week');
    expect(parsed[0].messages).toEqual([
      { role: 'dana', content: 'I noticed you wrote about stress. What does it feel like?', timestamp: 0 },
      { role: 'user', content: 'Exhausting honestly.', timestamp: 0 },
    ]);
  });

  it('survives malformed session attrs without losing messages', () => {
    const text = [
      '---\nversion: 2\ndate: 2026-07-04\n---',
      '<!-- dana:session not-json-at-all -->',
      '<!-- dana:msg role=dana -->\nstill here',
    ].join('\n\n');
    const parsed = store.parse(text);

    expect(parsed).toHaveLength(1);
    expect(parsed[0].messages[0].content).toBe('still here');
  });
});

describe('ConversationStore.localToday', () => {
  it('uses the LOCAL date, not UTC (regression: evening chats filed under tomorrow)', () => {
    // 8pm Pacific on July 4 = 4am UTC on July 5. localToday must say July 4.
    const RealDate = global.Date;
    class FakeDate extends RealDate {
      constructor() { super('2026-07-05T04:00:00.000Z'); }
      getFullYear() { return 2026; }
      getMonth() { return 6; } // July (0-indexed)
      getDate() { return 4; }
    }
    global.Date = FakeDate as DateConstructor;
    try {
      expect(store.localToday()).toBe('2026-07-04');
    } finally {
      global.Date = RealDate;
    }
  });
});
