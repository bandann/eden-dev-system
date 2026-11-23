# Third-party notices

## anti-slop

Eden's anti-slop layer (`rules/on-demand/eden-antislop-rules.md`, `skills/antislop/`) adapts
**anti-slop v3.2.21** (https://github.com/miqdadbadjuber/anti-slop, commit 69416cf).

- `skills/antislop/references/upstream/*.md` are the upstream skill texts, verbatim except for removed
  frontmatter and an added header.
- `scripts/contrast_check.py` is upstream `skills/antislop-human/contrast-check.py` with a changed
  self-test path and docstring.

MIT License, Copyright (c) 2026 Miqdad Badjuber (antislop). Full text:
`skills/antislop/references/upstream/LICENSE`.

## Ideas from gentle-ai (no code copied)

Eden 4.0 (beta) took design ideas from [gentle-ai](https://github.com/Gentleman-Programming/gentle-ai)
(Copyright (c) 2025 Gentleman Programming, MIT License): blocking reads of sensitive paths, delegating
only for a nameable reason, and keeping one capability table per AI tool. They were rewritten for Eden
in Python; no code, skill text or asset from that project is included. "Gentle AI" and "Engram" are its
authors' trademarks and are not used by Eden.

## UI/UX Pro Max (bundled)

`vendor/ui-ux-pro-max/` is a copy of the `ui-ux-pro-max` skill from
[UI/UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill), MIT License,
Copyright (c) 2024 Next Level Builder. Full text: `vendor/ui-ux-pro-max/LICENSE`. The upstream commit,
version and a checksum of every file are in `vendor/ui-ux-pro-max/VENDORED.json`. Changes: `SKILL.md`
renamed `UPSTREAM-SKILL.md` (kept as reference, not loaded as a skill) and `scripts/tests/` removed.
`/eden:uiux-pro` and `scripts/eden_uiux.py` run its search tool only after the dev's explicit yes.
