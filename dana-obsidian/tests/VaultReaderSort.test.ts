import { VaultReader } from '../src/VaultReader';

// readRecentEntries sorts by filename date (mtime fallback) — "recent" means
// recent DAYS, not recently touched files.

function file(path: string, mtime: number) {
  const name = path.split('/').pop() ?? path;
  return { path, basename: name.replace('.md', ''), stat: { mtime, ctime: 0, size: 0 } };
}

const LONG = 'A perfectly ordinary journal entry with enough characters to clear the minimum length gate for parsing.';

function makeApp(files: ReturnType<typeof file>[]) {
  return {
    vault: {
      getMarkdownFiles: () => files,
      cachedRead: async () => LONG,
    },
  } as any;
}

describe('VaultReader.readRecentEntries date-aware sort', () => {
  it('orders by filename date, not mtime (regression: editing an old note promoted it)', async () => {
    const files = [
      // old entry edited five minutes ago — huge mtime
      file('J/2026-01-01.md', 9_999_999_999_999),
      file('J/2026-07-03.md', 1000),
      file('J/2026-07-04.md', 500),
    ];
    const reader = new VaultReader(makeApp(files));

    const entries = await reader.readRecentEntries('J', 2);

    expect(entries.map(e => e.path)).toEqual(['J/2026-07-04.md', 'J/2026-07-03.md']);
  });

  it('falls back to mtime for files without a parseable date', async () => {
    const july4Local = new Date(2026, 6, 4).getTime();
    const files = [
      file('J/2026-07-01.md', 0),
      // undated note modified after July 1 but before July 4 (local midnights)
      file('J/random-thoughts.md', july4Local - 1000),
      file('J/2026-07-04.md', 0),
    ];
    const reader = new VaultReader(makeApp(files));

    const entries = await reader.readRecentEntries('J', 3);

    expect(entries.map(e => e.path)).toEqual([
      'J/2026-07-04.md',
      'J/random-thoughts.md',
      'J/2026-07-01.md',
    ]);
  });

  it('readPath returns null for a path that no longer exists', async () => {
    const app = {
      vault: {
        getAbstractFileByPath: () => null,
      },
    } as any;
    const reader = new VaultReader(app);

    expect(await reader.readPath('J/deleted.md')).toBeNull();
  });
});
