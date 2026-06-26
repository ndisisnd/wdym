---
name: Prompt Engineering Principles
description: Principles table used by prompt-engineer to select and apply targeted improvements to user prompts
type: reference
---

# Prompt Engineering Principles

Each principle targets a specific weakness. Principles are **additive** (add what is missing) or **subtractive** (remove what hurts). Apply 2–3 per prompt — never all at once.

Every principle row carries an **Exemplar**: a compact `before → after` showing the principle's effect in isolation. Use it as a pattern, not a template to copy verbatim.

This file has two layers:

- **Global base** — universal, academically-grounded principles. Always loaded. Used alone in `--global` / `mode = global`.
- **Type-specific principles** — domain principles loaded *on top of* the global base when the detection protocol (`refs/detect.md`) resolves a `prompt_type`. Selection then ranks across the **combined** pool (global base ∪ the one matching type section).

## Selection guide

Score each principle against the raw prompt before selecting:
- **Additive**: Does the prompt lack what this principle adds? → high score
- **Subtractive**: Does the prompt contain noise this principle removes? → high score
- Does the prompt already do this well, or lack the targeted noise? → skip

Subtractive principles always rank above additive ones when both apply: remove noise before adding structure. When a type section is loaded, a matching type-specific principle outranks a global one of equal score — the domain signal is stronger evidence.

---

# Global base

## Additive principles

| Principle | Description | When to apply | Exemplar |
|-----------|-------------|---------------|----------|
| Specificity | Add concrete details the original omits: format, length, audience, or constraints. | Prompt is vague ("help me with X", "write something about Y") | `write about dogs` → `Write a 200-word overview of common dog breeds for first-time owners.` |
| Goal specification | State what a good output looks like — not just what to do, but what success means. | No success criteria stated; output shape is unclear | `review my code` → `Review my code and list the top 3 issues by severity, each with a concrete fix.` |
| Positive instruction framing | Reframe passive or indirect requests into direct directives ("Write…", "List…", "Generate…"). **If the prompt gives only negative rules ("don't do X"), keep them but add the positive action to take.** | Prompt uses "can you", "help me", "I want you to"; **or** states only what *not* to do without saying what to do | `don't write long paragraphs` → `Write in short, scannable bullets. Avoid long paragraphs.` |
| Instruction ordering | Move the most important instruction to the start and restate the single key constraint at the end — models weight the first and last lines most (primacy/recency). | The core ask is buried in the middle of context or a long list of requirements | `[long context] … and keep it under 100 words.` → `Summarize in under 100 words. [context] … Stay under 100 words.` |
| Response leading / prefilling | Specify how the response must begin — or prefill its opening tokens — to lock the format and skip conversational preamble. | Output must start a specific way (JSON, a heading, "Yes/No"), or preamble should be suppressed | `give me the json` → `Return only JSON, no prose. Begin your reply with` `{` |
| Few-shot examples | Add 2–4 examples of the desired output before the request, with **consistent formatting**, **balanced labels**, and examples **closely matched** to the task — these design choices swing accuracy far more than example count alone. | Task is ambiguous; format is non-standard or highly specific | `classify these tickets` → `Classify each ticket. Examples (one per class): "Can't log in" → Critical; "Typo in footer" → Low.` |
| Role assignment | Assign a persona to steer **voice, tone, or style** — not to boost accuracy. Empirically, expert roles do *not* improve factual correctness and can reduce it on knowledge tasks. | Output needs a specific voice or register (e.g. a friendly mentor, a terse reviewer) — **not** for reasoning or factual tasks | `rewrite this rejection email` → `As a warm but direct hiring manager, rewrite this rejection email.` |
| Chain-of-thought elicitation | Ask the model to reason step-by-step before producing the answer. Pairing the request with one worked example (few-shot CoT) beats a bare "think step by step". | Task involves multi-step reasoning, maths, logic, or planning | `which database is faster?` → `Compare the two databases step by step, then state which is faster and why.` |
| Task decomposition | Instruct the model to break a complex task into explicit, labelled sub-problems and solve them in order — distinct from CoT's free-form reasoning. | Task bundles several distinct sub-tasks or a multi-stage deliverable | `build me a CLI todo app` → `Break this into parts — data model, command parser, storage, CLI — then implement each in order.` |
| Self-verification | Have the model draft an answer, check it against the requirements (or test it against examples), and correct errors before the final output. | Correctness matters and mistakes are costly or easy to miss | `write a regex for emails` → `Write the regex, test it on 3 valid and 3 invalid addresses, then fix any failures.` |
| Output format specification | Explicitly name the desired structure: list, table, JSON, prose, code block. | No output format is stated and the task supports multiple formats | `list the pros and cons` → `List the pros and cons as a two-column markdown table.` |
| Constraint injection | Add explicit boundaries: word count, tone, scope limits, what to exclude. | Prompt is open-ended; response risk of being too long, too broad, or off-topic | `explain quantum computing` → `Explain quantum computing in under 150 words, no equations.` |
| Audience framing | State who will read or use the output to calibrate vocabulary and depth. | Audience is non-default (a child, an expert, a non-technical stakeholder) | `explain APIs` → `Explain APIs to a non-technical product manager.` |
| Context priming | Provide relevant background the model needs but cannot infer from the prompt alone. | Prompt references "it", "this", "the project" without defining the referent | `why is it slow?` → `My Django list view runs 12 SQL queries per request. Why is it slow?` |
| Uncertainty escape hatch | Permit the model to say "I don't know", ask, or decline rather than guess. | Prompt demands a definitive answer on facts the model may not have | `what were Q3 2026 sales?` → `…If you don't have this figure, say so rather than guessing.` |

> **Out of scope — ensembling / self-consistency.** The Prompt Report's ensembling family (Self-Consistency, DiVeRSe) samples a prompt *multiple times* and votes on the majority answer. It is deliberately excluded here: this skill rewrites a single prompt and does not control sampling, so the technique cannot be expressed as a prompt edit.

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

# Type-specific principles

Loaded only when `refs/detect.md` resolves a `prompt_type`. Load the **one** section that matches, on top of the global base. The `type` column marks `additive` / `subtractive` for ranking against the global pool.

## Coding — `prompt_type = code`

| Principle | Type | Description | When to apply | Exemplar |
|-----------|------|-------------|---------------|----------|
| Language & version | additive | Name the language and runtime/version the code must target. | Language or version is unstated or implied | `parse a date` → `In Python 3.11, parse an ISO-8601 date string.` |
| I/O contract | additive | State inputs, outputs, types, and the function/CLI signature. | Shape of the interface is left open | `a function to sort users` → `def sort_users(users: list[User]) -> list[User] — sorted by signup date.` |
| Edge cases & errors | additive | Require handling of empty/invalid/boundary inputs and the failure behaviour. | Prompt asks only for the happy path | `divide two numbers` → `Divide two numbers; raise ValueError on divide-by-zero and non-numeric input.` |
| Test request | additive | Ask for unit tests or runnable usage examples alongside the code. | Correctness matters and no tests are requested | `write a slugify function` → `Write a slugify function plus pytest unit tests covering unicode and empty input.` |
| Dependency & style constraints | additive | Bound allowed libraries, style guide, and "no new dependencies" where relevant. | Open-ended; risk of pulling unwanted deps or off-house-style code | `fetch a URL` → `Fetch a URL using only the standard library — no new dependencies.` |
| Existing-code context | additive | Reference the surrounding code, framework, or file the change must fit. | Prompt says "it"/"this"/"the project" without showing the code | `fix the bug in it` → `Fix the off-by-one in the paginate() function below: …` |

## Question answering — `prompt_type = question`

| Principle | Type | Description | When to apply | Exemplar |
|-----------|------|-------------|---------------|----------|
| Depth calibration | additive | State desired depth and length (one line vs deep dive). | Ambiguous how thorough the answer should be | `tell me about Rome` → `Give a 3-sentence overview of why Rome fell.` |
| Sourcing & citations | additive | Ask for sources, or permit "I don't know" over a guess. | Factual accuracy is critical | `what year did this happen?` → `…Cite a source, or say if you're unsure.` |
| Scope & timeframe | additive | Bound the question's scope, region, or time period. | Question is broad or time-sensitive | `best phones?` → `Best flagship phones released in 2025, UK market.` |
| Audience level | additive | Set the reader's expertise to calibrate vocabulary and depth. | Audience is non-default (novice or specialist) | `explain inflation` → `Explain inflation to a 12-year-old.` |
| Reasoning elicitation | additive | Ask for step-by-step reasoning before the verdict on multi-step questions. | Answer depends on a chain of inference | `is this argument valid?` → `Assess each premise step by step, then judge if the argument holds.` |

## Language & text generation — `prompt_type = text-gen`

| Principle | Type | Description | When to apply | Exemplar |
|-----------|------|-------------|---------------|----------|
| Format & length | additive | Name the artifact and size (email, 200-word blurb, 5 bullets). | Output shape or length unstated | `write about our launch` → `Write a 5-bullet internal announcement of our launch.` |
| Tone & register | additive | Fix tone and formality for the channel. | Register undefined | `reply to this email` → `Reply in a warm but professional tone.` |
| Audience & purpose | additive | State the reader and the goal/CTA the text must achieve. | Purpose or reader unclear | `write a blurb` → `Write a blurb that gets enterprise buyers to book a demo.` |
| Fidelity constraint | additive | For translate/summarise/rewrite, require meaning preserved and key facts kept. | Task transforms an existing text | `summarize this report` → `Summarize this report; keep every figure and date accurate.` |
| Source-text anchoring | additive | Quote or attach the exact text to operate on. | Prompt refers to text not actually included | `make this shorter` → `Shorten the text below: "…"` |

---

## Worked examples

These show 2–3 principles combined on one prompt — the row-level Exemplars show each principle alone. Only a few **very distinct** transformation modes are kept here: noise removal (subtractive), formatted few-shot, and negative-only reframing.

### Positive instruction framing — negative-only prompt

**Before:** `don't make it sound robotic and don't use jargon`

**After:** `Write in a warm, conversational voice that a layperson can follow. Avoid robotic phrasing and jargon.`

**Principles applied:** Positive instruction framing (the negative rules are preserved, but a positive directive — *what to do* — is added in front), Audience framing (layperson).

---

### Few-shot examples

**Before:** `classify these support tickets by urgency`

**After:**
```
Classify each support ticket as Critical, High, Medium, or Low urgency.

Examples:
- "System is down, users cannot log in" → Critical
- "Export to CSV is slow" → Medium

Tickets to classify:
1. "Dashboard graphs are not loading"
2. "Billing shows wrong amount"
```

**Principles applied:** Few-shot examples (two labelled instances), Output format specification (four-level taxonomy).

---

### Subtractive — noise removal

**Before:** `Please please take a deep breath and think very hard. You are the world's best Python expert and my job depends on this. I'll tip you $200 if you write me a function to reverse a string. Thank you so much!!`

**After:** `Write a Python function that reverses a string.`

**Principles applied:** Politeness stripping ("please", "thank you"), Magic-phrase removal ("take a deep breath", "world's best expert", "think very hard"), Manipulation removal ("my job depends on this"), Bribe removal ("I'll tip you $200"). The underlying request — reverse a string — is preserved intact.

---

## Adding custom principles

Add rows to the table above. Follow the column format:
- **Principle**: short noun phrase (≤4 words)
- **Description**: what the principle adds to (or removes from) the prompt (≤20 words)
- **When to apply**: one observable trigger condition (≤15 words)
- **Exemplar**: a compact `before → after` showing the principle's effect in isolation
