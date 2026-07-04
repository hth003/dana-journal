# Dana — a private journaling family

Dana is a set of privacy-first journaling tools built around a single idea: your thoughts belong to you. All data stays local. No cloud, no tracking, no accounts.

![License](https://img.shields.io/badge/License-GPL%20v3-blue.svg)

---

## Two products, one spirit

### Dana Desktop [`dana-desktop/`](./dana-desktop/)

A standalone journaling application for macOS, Windows, and Linux. Runs entirely offline, including the AI — built with Python and Flet.

- Local AI insights via Qwen2.5-3B (downloads once, runs on your device)
- Interactive calendar, markdown editor, and SQLite-indexed entry management
- 4-step onboarding with dual vault modes (create new or load existing)
- Cross-platform: macOS .app, Windows .exe, Linux binary, and PWA

**Get started:** [`dana-desktop/README.md`](./dana-desktop/README.md)

---

### Dana for Obsidian [`dana-obsidian/`](./dana-obsidian/)

An Obsidian plugin that brings a warm journaling companion into your existing vault as a sidebar panel. Reads your notes, reflects with you, and saves conversations alongside your writing.

- Streaming AI reflections powered by Ollama (local) or OpenAI
- 9-state UI (IDLE → LOADING → STREAMING → CONVERSATION → ...)
- Conversation memory saved as `.dana/{date}-conversation.md` in your vault
- Prompt injection protection on all vault content passed to AI

**Get started:** [`dana-obsidian/README.md`](./dana-obsidian/README.md)

---

## Shared design language

Both products share the Dana identity:

| Token | Value | Use |
|-------|-------|-----|
| Primary (terracotta) | `#E07A5F` | Buttons, active states, accent |
| Secondary (sage) | `#81B29A` | Highlights, indicators |
| Journal format | YAML frontmatter + markdown | Entry files |
| Companion tone | Warm, specific, never preachy | All AI responses |

Dana never says "journey", "mindfulness", "wellness", or "AI-powered insights."

---

## Repository layout

```
journal_vault/
├── dana-desktop/     Python/Flet desktop app
│   ├── src/          Flet source (main.py, ui/, storage/, ai/, config/)
│   ├── tests/        pytest test suite
│   ├── scripts/      Build and release scripts
│   ├── docs/         Architecture, packaging, and PRD docs
│   └── pyproject.toml
└── dana-obsidian/    TypeScript Obsidian plugin
    ├── src/          Plugin source (DanaPanel, VaultReader, providers/)
    ├── tests/        Jest test suite
    ├── docs/         UX design spec and PRD
    ├── manifest.json
    └── package.json
```

---

## License

GNU General Public License v3.0 — see [LICENSE](./LICENSE).
