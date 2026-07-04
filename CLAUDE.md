# CLAUDE.md — journal_vault mono-repo

This repo contains two independent Dana products. Development guidance lives in each product's own CLAUDE.md:

- **Dana Desktop** (Python/Flet): [`dana-desktop/CLAUDE.md`](./dana-desktop/CLAUDE.md)
- **Dana for Obsidian** (TypeScript): see [`dana-obsidian/README.md`](./dana-obsidian/README.md#development) — development section covers all commands

## Repo layout

```
journal_vault/
├── dana-desktop/     Python 3.11+ / Flet desktop app
│   ├── src/          Flet source (main.py, ui/, storage/, ai/, config/)
│   ├── tests/        pytest suite
│   ├── scripts/      Build and release scripts
│   ├── docs/         Architecture, packaging, PRD
│   └── pyproject.toml
└── dana-obsidian/    TypeScript / Obsidian API plugin
    ├── src/          Plugin source (DanaPanel, VaultReader, providers/)
    ├── tests/        Jest suite
    ├── docs/         UX design spec and PRD
    ├── manifest.json
    └── package.json
```

## Git conventions

- Main branch: `main`
- Feature branches: `feature/<description>`
- Each product can be developed independently — changes in `dana-desktop/` don't affect `dana-obsidian/` and vice versa
- Use `uv` for all Python dependency management (never `pip` directly)
