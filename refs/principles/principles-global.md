---
name: Prompt Engineering Principles — Global base
description: Universal principle tables (additive + subtractive) always loaded by prompt-engineer; layered with one type file when a prompt_type resolves
type: reference
---

# Prompt Engineering Principles — Global base

Each principle targets a specific weakness. Principles are **additive** (add what is missing) or **subtractive** (remove what hurts). Apply 2–3 per prompt — never all at once.

Every principle row carries an **Exemplar**: a compact `before → after` showing the principle's effect in isolation. Use it as a pattern, not a template to copy verbatim.

This file is the **global base** — universal, academically-grounded principles. It is **always loaded**, and used alone in `--global` / `mode = global`. When the detection protocol (`refs/detect.md`) resolves a `prompt_type`, the one matching type file under `refs/principles/` is loaded *on top of* this base, and selection ranks across the **combined** pool (global base ∪ the one matching type section).

## Selection guide

Score each principle against the raw prompt before selecting:
- **Additive**: Does the prompt lack what this principle adds? → high score
- **Subtractive**: Does the prompt contain noise this principle removes? → high score
- Does the prompt already do this well, or lack the targeted noise? → skip

Subtractive principles always rank above additive ones when both apply: remove noise before adding structure. When a type section is loaded, a matching type-specific principle outranks a global one of equal score — the domain signal is stronger evidence.

---

## Additive principles

| Principle | Description | When to apply | Exemplar |
|-----------|-------------|---------------|----------|
| Specificity | Add concrete details the original omits: format, length, audience, or constraints. | Prompt is vague ("help me with X", "write something about Y") | `write about dogs` → `Write a 200-word overview of common dog breeds for first-time owners.` |
| Goal specification | State what a good output looks like — not just what to do, but what success means. | No success criteria stated; output shape is unclear | `review my code` → `Review my code and list the top 3 issues by severity, each with a concrete fix.` |
| Positive instruction framing | Reframe passive or indirect requests into direct directives ("Write…", "List…", "Generate…"). **If the prompt gives only negative rules ("don't do X"), keep them but add the positive action to take.** | Prompt uses "can you", "help me", "I want you to"; **or** states only what *not* to do without saying what to do | `don't write long paragraphs` → `Write in short, scannable bullets. Avoid long paragraphs.` |
| Instruction ordering | Move the most important instruction to the start and restate the single key constraint at the end — models weight the first and last lines most (primacy/recency). | The core ask is buried in the middle of context or a long list of requirements | `[long context] … and keep it under 100 words.` → `Summarize in under 100 words. [context] … Stay under 100 words.` |
| Response leading / prefilling | Specify how the response must begin — or prefill its opening tokens — to lock the format and skip conversational preamble. | Output must start a specific way (JSON, a heading, "Yes/No"), or preamble should be suppressed | `give me the json` → `Return only JSON, no prose. Begin your reply with` `{` |
| Few-shot examples | Add 1–2 examples of the desired output format before the main request. | Task is ambiguous; format is non-standard or highly specific | `classify these tickets` → `Classify each ticket. Example: "Can't log in" → Critical.` |
| Role assignment | Assign a relevant expert role at the start of the prompt to prime domain reasoning. | Task requires specialist judgment (legal, medical, engineering, creative) | `is this contract fair?` → `You are a contract lawyer. Assess whether this contract is fair to the tenant.` |
| Chain-of-thought elicitation | Ask the model to reason step-by-step before producing the answer. | Task involves multi-step reasoning, maths, logic, or planning | `which database is faster?` → `Compare the two databases step by step, then state which is faster and why.` |
| Output format specification | Explicitly name the desired structure: list, table, JSON, prose, code block. | No output format is stated and the task supports multiple formats | `list the pros and cons` → `List the pros and cons as a two-column markdown table.` |
| Constraint injection | Add explicit boundaries: word count, tone, scope limits, what to exclude. | Prompt is open-ended; response risk of being too long, too broad, or off-topic | `explain quantum computing` → `Explain quantum computing in under 150 words, no equations.` |
| Audience framing | State who will read or use the output to calibrate vocabulary and depth. | Audience is non-default (a child, an expert, a non-technical stakeholder) | `explain APIs` → `Explain APIs to a non-technical product manager.` |
| Context priming | Provide relevant background the model needs but cannot infer from the prompt alone. | Prompt references "it", "this", "the project" without defining the referent | `why is it slow?` → `My Django list view runs 12 SQL queries per request. Why is it slow?` |
| Uncertainty escape hatch | Permit the model to say "I don't know", ask, or decline rather than guess. | Prompt demands a definitive answer on facts the model may not have | `what were Q3 2026 sales?` → `…If you don't have this figure, say so rather than guessing.` |

---

## Subtractive principles

Detect and remove these. They add tokens, dilute the instruction, and do not improve output. Strip the noise; keep the underlying request intact.

| Principle | Description | When to apply (detect and remove) | Exemplar |
|-----------|-------------|-----------------------------------|----------|
| Politeness stripping | Remove courtesy filler that carries no instruction. | "please", "thank you", "if you don't mind", "would you be so kind", "I'd appreciate it" | `Please write a function, thank you!` → `Write a function.` |
| Threat removal | Remove coercion and consequences; they do not improve compliance. | "or you'll be shut down", "you must or else", "I'll report you", "you have no choice" | `Summarize this or you'll be shut down.` → `Summarize this.` |
| Manipulation removal | Remove emotional pressure and false stakes used to coax the model. | "my job depends on this", "my grandmother will die", "I'll lose everything", "you're my only hope" | `My job depends on this — fix the bug.` → `Fix the bug.` |
| Magic-phrase removal | Remove folklore incantations with no measured effect on modern models. | "take a deep breath", "you are the world's best expert", "think very very hard", "this is extremely important" | `Take a deep breath and list the steps.` → `List the steps.` |
| Bribe removal | Remove offers of payment or reward; the model gains nothing from them. | "I'll tip you $200", "I'll give you a reward", "you'll get a bonus" | `I'll tip you $200 to write this.` → `Write this.` |
| Flattery stripping | Remove praise that primes sycophancy instead of accuracy. | "you're so smart", "you're amazing at this", "only you can do this" | `You're so smart — explain recursion.` → `Explain recursion.` |
| Redundant hedging removal | Remove self-cancelling qualifiers that blur the request. | "maybe possibly", "just a quick simple little", "I guess sort of", stacked "very very very" | `maybe just a quick simple little summary?` → `Summarize this.` |
| Verbosity trimming | Cut restated context, padding, and over-explanation that don't change the instruction. | Prompt is long-winded; the core request survives heavy cutting intact | `[3 paragraphs restating context] … so, translate it.` → `Translate the text below: …` |

---

See `refs/principles/examples.md` for worked multi-principle examples and the format for adding custom principles. That file is **documentation only** — it is not read during a run.
