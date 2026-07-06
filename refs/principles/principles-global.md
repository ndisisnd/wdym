---
name: Prompt Engineering Principles — Global base
description: Universal principle tables (additive + subtractive) always loaded by wdym; layered with one type file when a prompt_type resolves
type: reference
---

# Prompt Engineering Principles — Global base

Each principle targets a specific weakness and is **additive** (adds what is missing) or **subtractive** (removes what hurts). Apply 2–3 per prompt, never all at once. Every row carries an **Exemplar** (`before → after`) — use it as a pattern, not a template to copy verbatim.

This is the **global base** — always loaded, and used alone in `--global` / `mode = global`. When a `prompt_type` resolves, its matching type file loads *on top of* this base and selection ranks across the combined pool. The full scoring and ranking rules live in protocol Step 4; within each table below, **rows are ordered by impact (highest first)** — a tie-break between equally-applicable principles only, never a reason to promote a barely-applicable one.

---

## Additive principles

| Principle | Description | When to apply | Exemplar |
|-----------|-------------|---------------|----------|
| Context priming | Provide relevant background the model needs but cannot infer from the prompt alone. | Prompt references "it", "this", "the project" without defining the referent | `why is it slow?` → `Why is [component/service] slow? It [describe observed symptom — e.g., times out after X seconds under Y load].` |
| Specificity | Add concrete details the original omits: format, length, audience, or constraints. | Prompt is vague ("help me with X", "write something about Y") | `write about dogs` → `Write a 200-word overview of common dog breeds for first-time owners.` |
| Goal specification | State what a good output looks like — not just what to do, but what success means. | No success criteria stated; output shape is unclear | `review my code` → `Review my code and list the top 3 issues by severity, each with a concrete fix.` |
| Constraint injection | Add explicit boundaries: word count, tone, scope limits, what to exclude. | Prompt is open-ended; response risk of being too long, too broad, or off-topic | `explain quantum computing` → `Explain quantum computing in under 150 words, no equations.` |
| Few-shot examples | Add 1–2 examples of the desired output format before the main request. | Task is ambiguous; format is non-standard or highly specific | `classify these tickets` → `Classify each ticket. Example: "Can't log in" → Critical.` |
| Output format specification | Explicitly name the desired structure: list, table, JSON, prose, code block. | No output format is stated and the task supports multiple formats | `list the pros and cons` → `List the pros and cons as a two-column markdown table.` |
| Audience framing | State who will read or use the output to calibrate vocabulary and depth. | Audience is non-default (a child, an expert, a non-technical stakeholder) | `explain APIs` → `Explain APIs to a non-technical product manager.` |
| Role assignment | Assign a relevant expert role at the start of the prompt to prime domain reasoning. | Task requires specialist judgment (legal, medical, engineering, creative) | `is this contract fair?` → `You are a contract lawyer. Assess whether this contract is fair to the tenant.` |
| Instruction ordering | Move the most important instruction to the start and restate the single key constraint at the end — models weight the first and last lines most (primacy/recency). | The core ask is buried in the middle of context or a long list of requirements | `[long context] … and keep it under 100 words.` → `Summarize in under 100 words. [context] … Stay under 100 words.` |
| Response leading / prefilling | Specify how the response must begin — or prefill its opening tokens — to lock the format and skip conversational preamble. | Output must start a specific way (JSON, a heading, "Yes/No"), or preamble should be suppressed | `give me the json` → `Return only JSON, no prose. Begin your reply with` `{` |
| Positive instruction framing | Reframe passive or indirect requests into direct directives ("Write…", "List…", "Generate…"). **If the prompt gives only negative rules ("don't do X"), keep them but add the positive action to take.** | Prompt uses "can you", "help me", "I want you to"; **or** states only what *not* to do without saying what to do | `don't write long paragraphs` → `Write in short, scannable bullets. Avoid long paragraphs.` |
| Chain-of-thought elicitation | Ask for the working to be shown before the answer. | **Narrow trigger:** only when the answer must display explicit multi-step calculation or logic for the user to check — modern models already reason internally by default | `which plan is cheaper for us?` → `Show the cost calculation for both plans, then state which is cheaper.` |
| Uncertainty escape hatch | Permit the model to say "I don't know", ask, or decline rather than guess. | Prompt demands a definitive answer on facts the model may not have | `what were Q3 2026 sales?` → `…If you don't have this figure, say so rather than guessing.` |

---

## Subtractive principles

Detect and remove these. They add tokens, dilute the instruction, and do not improve output. Strip the noise; keep the underlying request intact.

| Principle | Description | When to apply (detect and remove) | Exemplar |
|-----------|-------------|-----------------------------------|----------|
| Verbosity trimming | Cut restated context, padding, and over-explanation that don't change the instruction. | Prompt is long-winded; the core request survives heavy cutting intact | `[3 paragraphs restating context] … so, translate it.` → `Translate the text below: …` |
| Redundant hedging removal | Remove self-cancelling qualifiers that blur the request. | "maybe possibly", "just a quick simple little", "I guess sort of", stacked "very very very" | `maybe just a quick simple little summary?` → `Summarize this.` |
| Manipulation removal | Remove emotional pressure and false stakes used to coax the model. | "my job depends on this", "my grandmother will die", "I'll lose everything", "you're my only hope" | `My job depends on this — fix the bug.` → `Fix the bug.` |
| Threat removal | Remove coercion and consequences; they do not improve compliance. | "or you'll be shut down", "you must or else", "I'll report you", "you have no choice" | `Summarize this or you'll be shut down.` → `Summarize this.` |
| Magic-phrase removal | Remove folklore incantations with no measured effect on modern models. | "take a deep breath", "you are the world's best expert", "think very very hard", "this is extremely important" | `Take a deep breath and list the steps.` → `List the steps.` |
| Flattery stripping | Remove praise that primes sycophancy instead of accuracy. | "you're so smart", "you're amazing at this", "only you can do this" | `You're so smart — explain recursion.` → `Explain recursion.` |
| Bribe removal | Remove offers of payment or reward; the model gains nothing from them. | "I'll tip you $200", "I'll give you a reward", "you'll get a bonus" | `I'll tip you $200 to write this.` → `Write this.` |
| Politeness stripping | Remove courtesy filler that carries no instruction. | "please", "thank you", "if you don't mind", "would you be so kind", "I'd appreciate it" | `Please write a function, thank you!` → `Write a function.` |

---

## Worked examples

A **curated subset** — one example per pattern family (context, specificity, ordering, subtractive combo, trimming); every other principle is covered by its row-level **Exemplar** alone. Each example combines 2–3 principles on one prompt. Step 3 loads this section as flat reference context; Step 5 uses it alongside the row Exemplars as a bank of before→after patterns showing principles in combination. Use them as patterns, not templates to copy verbatim.

### Context priming

**Before:** `why does it keep crashing?`

**After:** `My [service/component] crashes [describe when — e.g., after ~2 hours / under high load], with [describe what you observe — e.g., no error in the logs / OOM signal]. Walk through the likely causes, then suggest what to instrument first.`

**Principles applied:** Context priming (placeholders mark where the user must supply runtime, workload, and symptom — never invent them), Chain-of-thought elicitation (walk through causes before recommending).

---

### Specificity

**Before:** `write me a function to parse dates`

**After:** `Write a Python function that parses date strings in ISO 8601 format (YYYY-MM-DD) and returns a datetime object. Raise ValueError with a descriptive message for invalid inputs. Include type hints and a docstring.`

**Principles applied:** Specificity (language, format, error handling), Output format specification (function with docstring).

---

### Instruction ordering

**Before:** `Here's my situation: we're a small team, budget is tight, we've used AWS before but found it complex, we need something for a side project that might grow, and we want to deploy a web app — what platform should we use? Keep it brief.`

**After:** `Recommend one deployment platform for a web app, in 3 sentences max. Context: small team, tight budget, prior AWS experience felt too complex, side project that may grow. End with your single recommendation and why.`

**Principles applied:** Instruction ordering (the core ask moves to the front and the key constraint is restated at the end), Constraint injection (3 sentences).

---

### Subtractive — noise removal

**Before:** `Please please take a deep breath and think very hard. You are the world's best Python expert and my job depends on this. I'll tip you $200 if you write me a function to reverse a string. Thank you so much!!`

**After:** `Write a Python function that reverses a string.`

**Principles applied:** Politeness stripping ("please", "thank you"), Magic-phrase removal ("take a deep breath", "world's best expert", "think very hard"), Manipulation removal ("my job depends on this"), Bribe removal ("I'll tip you $200"). The underlying request — reverse a string — is preserved intact.

---

### Verbosity trimming

**Before:** `So I've been working on this report for a while now, it's about our Q2 numbers, and there's a lot of context here that I won't bore you with, but basically the gist is I have this long document and I really need it condensed down — could you summarize it for me?`

**After:** `Summarize the Q2 report below in 5 bullets: …`

**Principles applied:** Verbosity trimming (restated context and self-narration cut), Output format specification (5 bullets).

---

## Adding custom principles

See `refs/authoring.md` for the column format and how to append a worked example.
