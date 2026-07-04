# TODOS — Dana for Obsidian

## P2 — Standalone free-chat entry point with vault-wide retrieval (v1.1)

- **What:** Third idle-screen option "Ask Dana" — open-ended chat grounded in
  local embeddings over the whole vault (top-k relevant notes injected per
  question), not just recent entries.
- **Why:** User feedback explicitly asked for a free-flow option that "answers
  based on what they know in the Obsidian vault." Deferred from the 2026-07-04
  MVP simplification because none of the reported trust/grounding bugs required
  it, and honest retrieval needs an embedding pipeline.
- **Pros:** Completes the 3-option product vision (entry / week / free);
  the `ReflectionMode` plumbing from the MVP plan was designed as its extension
  point (`mode: 'chat'`).
- **Cons:** First WASM/embedding dependency (~25MB model download UX), indexing
  performance on large vaults, re-index-on-change complexity.
- **Context:** See `docs/superpowers/plans/2026-07-04-dana-mvp-simplification-plan.md`
  ("NOT in scope"). The in-conversation reply box already provides free chat
  *within* a grounded session; this item is the standalone vault-wide entry point.
  Candidate approach: Transformers.js MiniLM embeddings cached per-file by mtime.
- **Effort:** L (human ~2 weeks / CC+gstack ~3-4 hours)
- **Depends on:** MVP simplification plan (ReflectionMode, conversation-scoped
  context cache) landing first.
