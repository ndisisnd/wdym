---
name: Prompt Engineering Principles
description: Principles table used by prompt-engineer to select and apply targeted improvements to user prompts
type: reference
---

# Prompt Engineering Principles

Each principle targets a specific weakness. Principles are **additive** (add what is missing) or **subtractive** (remove what hurts). Apply 2–3 per prompt — never all at once.

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

| Principle | Description | When to apply |
|-----------|-------------|---------------|
| Specificity | Add concrete details the original omits: format, length, audience, or constraints. | Prompt is vague ("help me with X", "write something about Y") |
| Goal specification | State what a good output looks like — not just what to do, but what success means. | No success criteria stated; output shape is unclear |
| Positive instruction framing | Reframe passive or indirect requests into direct directives ("Write…", "List…", "Generate…"). | Prompt uses "can you", "help me", "I want you to" |
| Few-shot examples | Add 1–2 examples of the desired output format before the main request. | Task is ambiguous; format is non-standard or highly specific |
| Role assignment | Assign a relevant expert role at the start of the prompt to prime domain reasoning. | Task requires specialist judgment (legal, medical, engineering, creative) |
| Chain-of-thought elicitation | Ask the model to reason step-by-step before producing the answer. | Task involves multi-step reasoning, maths, logic, or planning |
| Output format specification | Explicitly name the desired structure: list, table, JSON, prose, code block. | No output format is stated and the task supports multiple formats |
| Constraint injection | Add explicit boundaries: word count, tone, scope limits, what to exclude. | Prompt is open-ended; response risk of being too long, too broad, or off-topic |
| Audience framing | State who will read or use the output to calibrate vocabulary and depth. | Audience is non-default (a child, an expert, a non-technical stakeholder) |
| Context priming | Provide relevant background the model needs but cannot infer from the prompt alone. | Prompt references "it", "this", "the project" without defining the referent |
| Uncertainty escape hatch | Permit the model to say "I don't know", ask, or decline rather than guess. | Prompt demands a definitive answer on facts the model may not have |

---

## Subtractive principles

Detect and remove these. They add tokens, dilute the instruction, and do not improve output. Strip the noise; keep the underlying request intact.

| Principle | Description | When to apply (detect and remove) |
|-----------|-------------|-----------------------------------|
| Politeness stripping | Remove courtesy filler that carries no instruction. | "please", "thank you", "if you don't mind", "would you be so kind", "I'd appreciate it" |
| Threat removal | Remove coercion and consequences; they do not improve compliance. | "or you'll be shut down", "you must or else", "I'll report you", "you have no choice" |
| Manipulation removal | Remove emotional pressure and false stakes used to coax the model. | "my job depends on this", "my grandmother will die", "I'll lose everything", "you're my only hope" |
| Magic-phrase removal | Remove folklore incantations with no measured effect on modern models. | "take a deep breath", "you are the world's best expert", "think very very hard", "this is extremely important" |
| Bribe removal | Remove offers of payment or reward; the model gains nothing from them. | "I'll tip you $200", "I'll give you a reward", "you'll get a bonus" |
| Flattery stripping | Remove praise that primes sycophancy instead of accuracy. | "you're so smart", "you're amazing at this", "only you can do this" |
| Redundant hedging removal | Remove self-cancelling qualifiers that blur the request. | "maybe possibly", "just a quick simple little", "I guess sort of", stacked "very very very" |
| Verbosity trimming | Cut restated context, padding, and over-explanation that don't change the instruction. | Prompt is long-winded; the core request survives heavy cutting intact |

---

# Type-specific principles

Loaded only when `refs/detect.md` resolves a `prompt_type`. Load the **one** section that matches, on top of the global base. The `type` column marks `additive` / `subtractive` for ranking against the global pool.

## Coding — `prompt_type = code`

| Principle | Type | Description | When to apply |
|-----------|------|-------------|---------------|
| Language & version | additive | Name the language and runtime/version the code must target. | Language or version is unstated or implied |
| I/O contract | additive | State inputs, outputs, types, and the function/CLI signature. | Shape of the interface is left open |
| Edge cases & errors | additive | Require handling of empty/invalid/boundary inputs and the failure behaviour. | Prompt asks only for the happy path |
| Test request | additive | Ask for unit tests or runnable usage examples alongside the code. | Correctness matters and no tests are requested |
| Dependency & style constraints | additive | Bound allowed libraries, style guide, and "no new dependencies" where relevant. | Open-ended; risk of pulling unwanted deps or off-house-style code |
| Existing-code context | additive | Reference the surrounding code, framework, or file the change must fit. | Prompt says "it"/"this"/"the project" without showing the code |

## Creative writing — `prompt_type = creative-writing`

| Principle | Type | Description | When to apply |
|-----------|------|-------------|---------------|
| Voice, POV & tense | additive | Fix narrative point of view, tense, and narrator voice. | Unspecified; output could drift in person/tense |
| Genre & tone | additive | Name the genre and emotional register (comic, noir, wistful…). | Tone is undefined |
| Form & length | additive | Set the structural unit: word count, stanzas, scenes, acts. | No length or form given |
| Constraint seeding | additive | Supply 1–3 concrete anchors (setting, character, conflict) to ground invention. | Prompt is a bare premise |
| Over-direction trimming | subtractive | Cut excessive micro-instructions that strangle the creative space. | Prompt over-specifies every beat, leaving no room to write |

## Image generation — `prompt_type = image-gen`

| Principle | Type | Description | When to apply |
|-----------|------|-------------|---------------|
| Subject & composition | additive | State the main subject plus foreground/background and framing. | Subject or layout is vague |
| Style & medium | additive | Name the medium and style (photo, oil painting, 3D render, line art). | No visual style specified |
| Lighting & palette | additive | Specify lighting, mood, and colour palette. | Atmosphere undefined |
| Camera & lens | additive | For photoreal output, give shot type, angle, lens, depth of field. | Photorealism wanted but camera unspecified |
| Technical params | additive | Add aspect ratio, resolution, and a negative prompt (what to exclude). | Output dimensions / exclusions matter and are missing |
| Conversational stripping | subtractive | Drop "please draw me / can you make" — image models want noun phrases, not requests. | Prompt is phrased as a chat request rather than a scene description |

## Question answering — `prompt_type = question`

| Principle | Type | Description | When to apply |
|-----------|------|-------------|---------------|
| Depth calibration | additive | State desired depth and length (one line vs deep dive). | Ambiguous how thorough the answer should be |
| Sourcing & citations | additive | Ask for sources, or permit "I don't know" over a guess. | Factual accuracy is critical |
| Scope & timeframe | additive | Bound the question's scope, region, or time period. | Question is broad or time-sensitive |
| Audience level | additive | Set the reader's expertise to calibrate vocabulary and depth. | Audience is non-default (novice or specialist) |
| Reasoning elicitation | additive | Ask for step-by-step reasoning before the verdict on multi-step questions. | Answer depends on a chain of inference |

## Language & text generation — `prompt_type = text-gen`

| Principle | Type | Description | When to apply |
|-----------|------|-------------|---------------|
| Format & length | additive | Name the artifact and size (email, 200-word blurb, 5 bullets). | Output shape or length unstated |
| Tone & register | additive | Fix tone and formality for the channel. | Register undefined |
| Audience & purpose | additive | State the reader and the goal/CTA the text must achieve. | Purpose or reader unclear |
| Fidelity constraint | additive | For translate/summarise/rewrite, require meaning preserved and key facts kept. | Task transforms an existing text |
| Source-text anchoring | additive | Quote or attach the exact text to operate on. | Prompt refers to text not actually included |

---

## Worked examples

### Specificity

**Before:** `write me a function to parse dates`

**After:** `Write a Python function that parses date strings in ISO 8601 format (YYYY-MM-DD) and returns a datetime object. Raise ValueError with a descriptive message for invalid inputs. Include type hints and a docstring.`

**Principles applied:** Specificity (language, format, error handling), Output format specification (function with docstring).

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

### Chain-of-thought elicitation

**Before:** `should we use PostgreSQL or MongoDB for this project?`

**After:** `We are building a multi-tenant SaaS app with structured user profiles and frequent complex joins. Think through the trade-offs between PostgreSQL and MongoDB — consider schema flexibility, query patterns, and operational complexity — then give a recommendation with a one-sentence rationale.`

**Principles applied:** Context priming (project type), Chain-of-thought elicitation (think through trade-offs first), Goal specification (recommendation + rationale).

---

### Subtractive — noise removal

**Before:** `Please please take a deep breath and think very hard. You are the world's best Python expert and my job depends on this. I'll tip you $200 if you write me a function to reverse a string. Thank you so much!!`

**After:** `Write a Python function that reverses a string.`

**Principles applied:** Politeness stripping ("please", "thank you"), Magic-phrase removal ("take a deep breath", "world's best expert", "think very hard"), Manipulation removal ("my job depends on this"), Bribe removal ("I'll tip you $200"). The underlying request — reverse a string — is preserved intact.

---

## Adding custom principles

Add rows to the table above. Follow the column format:
- **Principle**: short noun phrase (≤4 words)
- **Description**: what the principle adds to the prompt (≤20 words)
- **When to apply**: one observable trigger condition (≤15 words)
