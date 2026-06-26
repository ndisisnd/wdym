# Changelog

All notable changes to this project will be documented here.

## 2026-06-26

Added `comprehensive` and `flash` run modes to the `prompt-engineer` skill. The mode is stored permanently as a key-value pair in a new `pref.json` at the skill root, which the protocol now scans first (Step 0) on every run. Comprehensive mode (the default) presents the transformed prompt for approval and then asks whether to run it; flash mode rewrites and runs immediately with no gates. The mode switches permanently via `/wdym --set-mode --flash` / `--comprehensive` (or inline `--flash` / `--comprehensive` flags). Steps 6 and 7 are now mode-aware. When a comprehensive-mode session ends in terminate, the skill now emits a hint suggesting flash mode.

Added an empty `README.md` placeholder at the repo root.

Added prompt-type detection routing to the `prompt-engineer` skill. A deterministic `UserPromptSubmit` pre-scorer (`hooks/prompt-detect.py`) scores each prompt against a shared type taxonomy (`refs/categories.json`) and injects a `<prompt-detect>` block; the new detection protocol (`refs/detect.md`) consumes it, handles the `--global` escape hatch, and resolves a `prompt_type` (code, creative-writing, image-gen, question, text-gen, or none). Principles now layer a global base plus type-specific sections, and the protocol expands from six to seven steps. Detection hook wired in `.claude/settings.json`.

## 2026-06-24

Initialized the `prompt-engineer` skill — a `UserPromptSubmit` hook that automatically classifies, rewrites, and presents enhanced versions of user prompts before execution. Ships with a principles table (additive and subtractive) and a six-step protocol driving the full classify → select → rewrite → approve flow. Kermit changelog tooling also initialized.
