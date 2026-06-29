---
name: Prompt Engineering Principles — Global base
description: Universal principle tables (additive + subtractive) always loaded by wdym; layered with one type file when a prompt_type resolves
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

**Rows are ordered by impact, highest first** (within each table — additive, subtractive, and every type file). The order encodes a static prior on how much a principle improves output *when it applies*; it does **not** override applicability. Use it only as a tie-break: when two applicable principles score equally on relevance, prefer the one listed earlier. Never promote a barely-applicable high-row principle over a clearly-applicable lower one.

---

## Additive principles

| Principle | Description | When to apply | Exemplar |
|-----------|-------------|---------------|----------|
| Context priming | Provide relevant background the model needs but cannot infer from the prompt alone. | Prompt references "it", "this", "the project" without defining the referent | `why is it slow?` → `Why is [component/service] slow? It [describe observed symptom — e.g., times out after X seconds under Y load].` |
| Specificity | Add concrete details the original omits: format, length, audience, or constraints. | Prompt is vague ("help me with X", "write something about Y") | `write about dogs` → `Write a 200-word overview of common dog breeds for first-time owners.` |
| Goal specification | State what a good output looks like — not just what to do, but what success means. | No success criteria stated; output shape is unclear | `review my code` → `Review my code and list the top 3 issues by severity, each with a concrete fix.` |
| Constraint injection | Add explicit boundaries: word count, tone, scope limits, what to exclude. | Prompt is open-ended; response risk of being too long, too broad, or off-topic | `explain quantum computing` → `Explain quantum computing in under 150 words, no equations.` |
| Chain-of-thought elicitation | Ask the model to reason step-by-step before producing the answer. | Task involves multi-step reasoning, maths, logic, or planning | `which database is faster?` → `Compare the two databases step by step, then state which is faster and why.` |
| Few-shot examples | Add 1–2 examples of the desired output format before the main request. | Task is ambiguous; format is non-standard or highly specific | `classify these tickets` → `Classify each ticket. Example: "Can't log in" → Critical.` |
| Output format specification | Explicitly name the desired structure: list, table, JSON, prose, code block. | No output format is stated and the task supports multiple formats | `list the pros and cons` → `List the pros and cons as a two-column markdown table.` |
| Audience framing | State who will read or use the output to calibrate vocabulary and depth. | Audience is non-default (a child, an expert, a non-technical stakeholder) | `explain APIs` → `Explain APIs to a non-technical product manager.` |
| Role assignment | Assign a relevant expert role at the start of the prompt to prime domain reasoning. | Task requires specialist judgment (legal, medical, engineering, creative) | `is this contract fair?` → `You are a contract lawyer. Assess whether this contract is fair to the tenant.` |
| Instruction ordering | Move the most important instruction to the start and restate the single key constraint at the end — models weight the first and last lines most (primacy/recency). | The core ask is buried in the middle of context or a long list of requirements | `[long context] … and keep it under 100 words.` → `Summarize in under 100 words. [context] … Stay under 100 words.` |
| Response leading / prefilling | Specify how the response must begin — or prefill its opening tokens — to lock the format and skip conversational preamble. | Output must start a specific way (JSON, a heading, "Yes/No"), or preamble should be suppressed | `give me the json` → `Return only JSON, no prose. Begin your reply with` `{` |
| Positive instruction framing | Reframe passive or indirect requests into direct directives ("Write…", "List…", "Generate…"). **If the prompt gives only negative rules ("don't do X"), keep them but add the positive action to take.** | Prompt uses "can you", "help me", "I want you to"; **or** states only what *not* to do without saying what to do | `don't write long paragraphs` → `Write in short, scannable bullets. Avoid long paragraphs.` |
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

Each worked example combines 2–3 principles on one prompt; the row-level **Exemplars** in the tables above show each principle alone. Step 3 loads this section as flat reference context; Step 5 uses it alongside the row Exemplars as a bank of before→after patterns showing principles in combination. Use them as patterns, not templates to copy verbatim.

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

### Goal specification

**Before:** `look over my onboarding flow`

**After:** `Review my onboarding flow and tell me the single biggest drop-off risk, with one concrete change that would reduce it. A good answer names the step, the reason users abandon it, and the fix.`

**Principles applied:** Goal specification (spells out what a good answer contains), Constraint injection (one risk, one change).

---

### Constraint injection

**Before:** `explain how OAuth works`

**After:** `Explain how the OAuth 2.0 authorization-code flow works in under 200 words, no diagrams, assuming I already know what an access token is.`

**Principles applied:** Constraint injection (length cap, exclude diagrams, scope limit), Audience framing (reader already knows access tokens).

---

### Chain-of-thought elicitation

**Before:** `should we use PostgreSQL or MongoDB for this project?`

**After:** `We are building a multi-tenant SaaS app with structured user profiles and frequent complex joins. Think through the trade-offs between PostgreSQL and MongoDB — consider schema flexibility, query patterns, and operational complexity — then give a recommendation with a one-sentence rationale.`

**Principles applied:** Context priming (project type), Chain-of-thought elicitation (think through trade-offs first), Goal specification (recommendation + rationale).

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

### Output format specification

**Before:** `compare the three plans`

**After:** `Compare the Free, Pro, and Enterprise plans as a markdown table — one row per feature, one column per plan. End with a one-line recommendation for a 10-person startup.`

**Principles applied:** Output format specification (markdown table, row/column layout), Audience framing (10-person startup).

---

### Audience framing

**Before:** `explain what a vector database is`

**After:** `Explain what a vector database is to a non-technical executive deciding whether to fund one. Skip the maths; focus on what it enables and when it's worth the cost.`

**Principles applied:** Audience framing (non-technical executive), Constraint injection (skip the maths, focus on value).

---

### Role assignment

**Before:** `is this lease clause normal?`

**After:** `You are a tenant-rights lawyer. Review the lease clause below and tell me whether it's standard, unusual, or unenforceable, and what to push back on: "…"`

**Principles applied:** Role assignment (tenant-rights lawyer primes domain reasoning), Goal specification (standard / unusual / unenforceable verdict + what to push back on).

---

### Instruction ordering

**Before:** `Here's my situation: we're a small team, budget is tight, we've used AWS before but found it complex, we need something for a side project that might grow, and we want to deploy a web app — what platform should we use? Keep it brief.`

**After:** `Recommend one deployment platform for a web app, in 3 sentences max. Context: small team, tight budget, prior AWS experience felt too complex, side project that may grow. End with your single recommendation and why.`

**Principles applied:** Instruction ordering (the core ask moves to the front and the key constraint is restated at the end), Constraint injection (3 sentences).

---

### Response leading / prefilling

**Before:** `give me the config as json`

**After:** ``Return only the config as JSON — no prose, no markdown fences. Begin your reply with `{`.``

**Principles applied:** Response leading / prefilling (locks the opening token and suppresses preamble), Output format specification (JSON only).

---

### Positive instruction framing — negative-only prompt

**Before:** `don't make it sound robotic and don't use jargon`

**After:** `Write in a warm, conversational voice that a layperson can follow. Avoid robotic phrasing and jargon.`

**Principles applied:** Positive instruction framing (the negative rules are preserved, but a positive directive — *what to do* — is added in front), Audience framing (layperson).

---

### Uncertainty escape hatch

**Before:** `what's the market size for AI legal tools in 2027?`

**After:** `Estimate the 2027 market size for AI legal tools. State your assumptions and show the calculation. If you don't have reliable figures, say so and give a clearly-labelled rough range rather than a confident number.`

**Principles applied:** Uncertainty escape hatch (permits a labelled estimate over a false-precise guess), Chain-of-thought elicitation (state assumptions, show the calculation).

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

### Redundant hedging removal

**Before:** `maybe could you possibly just give me a sort of quick rough idea of how to maybe start learning Rust?`

**After:** `Give me a concrete first-week plan for learning Rust.`

**Principles applied:** Redundant hedging removal (stacked "maybe / possibly / just / sort of / quick rough" cut), Specificity (a first-week plan instead of a vague "idea").

---

### Threat removal

**Before:** `Rewrite this paragraph and do it right or I'm reporting you and switching to another AI.`

**After:** `Rewrite the paragraph below for clarity: "…"`

**Principles applied:** Threat removal (the coercion and consequence add nothing to compliance), Goal specification (the success criterion — rewrite for clarity — is stated plainly).

---

### Flattery stripping

**Before:** `You're honestly the smartest AI I've ever used and way better than the others — only you could pull this off — can you design a caching strategy for my API?`

**After:** `Design a caching strategy for my REST API: read-heavy, ~500 req/s, data tolerates 60s staleness.`

**Principles applied:** Flattery stripping (praise primes sycophancy, removed), Context priming (load profile and staleness tolerance the strategy depends on).

---

## Adding custom principles

Add rows to the appropriate file — global principles here, domain principles to the matching `principles-<type>.md`. Follow the column format:
- **Principle**: short noun phrase (≤4 words)
- **Description**: what the principle adds to (or removes from) the prompt (≤20 words)
- **When to apply**: one observable trigger condition (≤15 words)
- **Exemplar**: a compact `before → after` showing the principle's effect in isolation

Type files also carry a **Type** column (`additive` / `subtractive`) used to rank against the global pool. When you add a principle, you may also append a matching worked example to that file's **Worked examples** section — keyed by the principle name, combining it with 1–2 companions.
