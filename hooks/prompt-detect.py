#!/usr/bin/env python3
"""UserPromptSubmit pre-scorer for the wdym skill.

Deterministic keyword/regex classifier. Reads the submitted prompt, scores it
against refs/categories.json, and injects a <prompt-detect> block as additional
context. The skill's detect protocol (refs/detect.md, Step 2) consumes this:
trust the verdict when `clear`, adjudicate among `candidates` when `ambiguous`.

Contract: never block or mutate the prompt. A broken scorer never drops the
prompt. Where it can still identify the prompt (stdin parsed, prompt non-empty)
but its config is unusable, it emits a self-reporting `verdict: degraded` block
instead of exiting silently — so the skill's self-check (protocol Step 0.5) can
tell "hook ran but config is broken" apart from "hook never ran" and heal the
config. Only failures that leave nothing to report (bad stdin, empty prompt)
exit 0 with no output.

Passthrough prompts (slash command / <=5 words / conversational follow-up) get
NO block at all — only a telemetry line. This makes the contract binary: block
present => substantive prompt => the ACTION line in the block instructs the
model to invoke the wdym skill. Block absent => respond normally.

Token-efficiency duties absorbed from the skill (each deletes an LLM tool call,
i.e. a full-context API round trip):
  - run_mode:   resolves pref.json (local over global) into a `run_mode:` block
                line, so the skill never reads the pref on the happy path.
  - selfcheck:  probes the required files; a `selfcheck:` line appears ONLY on
                failure — the skill reads refs/heal.md then, and otherwise
                skips its own probe entirely.
  - telemetry:  in flash mode with a clear/global verdict the outcome is
                deterministically "run", so the hook pre-logs the src:"skill"
                line and marks the block `telemetry: logged`; the skill skips
                its Step 8 append.
  - well_formed skip: a prompt that already carries structure (imperative
                opening plus >=2 of numeric constraint / format / audience /
                success criteria) and zero noise cues gets no block at all — a
                rewrite would not improve it. Tunable via categories.json
                `well_formed`; logged with verdict "skip".
"""

import json
import os
import re
import sys
from datetime import datetime, timezone


# --- Telemetry (hybrid stream A: deterministic per-submission log) -----------
#
# Appends one {"src":"hook", ...} line per submission to the resolved
# wdym/telemetry.jsonl, colocated with pref.json (local scope overrides global).
# Best-effort and isolated: any failure is swallowed so telemetry can never
# block or drop a prompt. The skill's Step 8 writes the matching {"src":"skill"}
# outcome line; refs/protocol.md `--stats` aggregates both streams.

FOLLOWUP_PREFIXES = (
    "thanks", "thank you", "ok", "got it", "sounds good", "sure", "and", "also",
)
FOLLOWUP_EXACT = ("can you elaborate", "what about", "go on", "continue")


def is_passthrough(raw: str) -> bool:
    """Replicate protocol Step 1's deterministic passthrough conditions so the
    hook can flag prompts the skill will skip (slash / <=5 words / follow-up)."""
    s = raw.strip()
    if s.startswith("/"):
        return True
    if len(s.split()) <= 5:
        return True
    low = s.lower().rstrip(".!?").strip()
    if low in FOLLOWUP_EXACT:
        return True
    # Prefix must end at a word boundary — "thanks, that works" matches,
    # "also-ran analysis" does not ("also" is followed by a hyphenated word).
    if any(re.match(rf"{re.escape(p)}([\s,!.:;]|$)", low) for p in FOLLOWUP_PREFIXES):
        return True
    return False


def telemetry_path():
    """Resolve wdym/telemetry.jsonl at the active install scope: local
    .claude/wdym/ overrides global ~/.claude/wdym/. Returns None if neither
    install dir exists (the dir is created by --init, never by the hook)."""
    candidates = []
    proj = os.environ.get("CLAUDE_PROJECT_DIR")
    if proj:
        candidates.append(os.path.join(proj, ".claude", "wdym"))
    candidates.append(os.path.join(os.getcwd(), ".claude", "wdym"))
    candidates.append(os.path.expanduser("~/.claude/wdym"))
    for d in candidates:
        if os.path.isdir(d):
            return os.path.join(d, "telemetry.jsonl")
    return None


def log_telemetry(record: dict) -> None:
    try:
        path = telemetry_path()
        if not path:
            return
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, separators=(",", ":")) + "\n")
    except Exception:
        pass


def resolve_run_mode():
    """Resolve pref.json local-first (same order as telemetry_path). Returns
    (run_mode, pref_wound): mode defaults to 'comprehensive'; pref_wound is a
    selfcheck note when a pref exists but is invalid (skill heals via heal.md).
    """
    candidates = []
    proj = os.environ.get("CLAUDE_PROJECT_DIR")
    if proj:
        candidates.append(os.path.join(proj, ".claude", "wdym", "pref.json"))
    candidates.append(os.path.join(os.getcwd(), ".claude", "wdym", "pref.json"))
    candidates.append(os.path.expanduser("~/.claude/wdym/pref.json"))
    for p in candidates:
        if not os.path.isfile(p):
            continue
        try:
            with open(p, "r", encoding="utf-8") as fh:
                mode = json.load(fh).get("mode")
            if mode in ("comprehensive", "flash"):
                return mode, None
            return "comprehensive", "pref invalid"
        except Exception:
            return "comprehensive", "pref unparseable"
    return "comprehensive", None


SELFCHECK_FILES = (  # relative to the skill root; categories.json has its own path
    "refs/categories.default.json",
    "refs/principles/principles-global.md",
    "refs/protocol.md",
    "refs/heal.md",
    "hooks/telemetry-stats.py",
)


def selfcheck(root: str):
    """Existence probe the skill used to burn a Bash call on. Returns the list
    of missing required files (empty = healthy)."""
    return [f for f in SELFCHECK_FILES
            if not os.path.isfile(os.path.join(root, f))]


# --- well-formed skip gate ----------------------------------------------------
# A prompt that already reads like a finished instruction gains nothing from a
# rewrite; suppressing the block skips the whole skill invocation. Conservative
# by design: imperative opening + >=2 structure signals + zero noise cues.

IMPERATIVE_OPENERS = (
    "write", "list", "summarize", "summarise", "explain", "draft", "generate",
    "create", "implement", "refactor", "fix", "review", "translate", "rewrite",
    "compare", "produce", "return", "give", "make", "add", "convert",
    "extract", "classify", "update", "describe", "outline", "analyze",
    "analyse", "recommend",
)
SIGNAL_PATTERNS = (
    # numeric constraint
    r"\b\d+[- ]?(words?|bullets?|sentences?|lines?|items?|paragraphs?|points?|steps?|examples?|issues?)\b",
    r"\b(under|at most|max(imum)?|no more than|top|within) \d+\b",
    # explicit format
    r"\b(as|in|into) (a |an )?(two-column )?(table|json|yaml|csv|markdown|numbered list|code block)\b",
    # audience
    r"\b(for|to) (a |an )?(beginners?|experts?|child(ren)?|non-technical|technical|first-time|new|novice|junior|senior|\d+-year-old)\b",
    # success criteria / ordering
    r"\b(ranked by|ordered by|sorted by|by severity|by priority|each with)\b",
)
NOISE_CUES = (
    "please", "thank", "could you", "can you", "would you", "help me",
    "i think", "maybe", "sorry", "i want you", "i need you", "take a deep breath",
    "tip you",
)


def is_well_formed(text: str, cfg: dict) -> bool:
    wf = cfg.get("well_formed", {})
    if not wf.get("enabled", False):
        return False
    first = re.split(r"[^a-z']+", text.strip(), 1)[0]
    if first not in IMPERATIVE_OPENERS:
        return False
    if any(cue_match(c, text) for c in NOISE_CUES):
        return False
    signals = sum(1 for p in SIGNAL_PATTERNS if re.search(p, text))
    return signals >= wf.get("min_extra_signals", 2)


def cue_match(term: str, text: str) -> bool:
    """Substring match with alphanumeric boundaries so 'go' != 'good',
    while symbol-bearing terms like 'c++' or 'tl;dr' still match."""
    pat = re.escape(term.strip())
    left = r"(?<![a-z0-9])" if term.strip()[:1].isalnum() else ""
    right = r"(?![a-z0-9])" if term.strip()[-1:].isalnum() else ""
    return re.search(left + pat + right, text) is not None


def score_category(cat: dict, text: str) -> int:
    """Count distinct matched cues. Each keyword/phrase counts at most once;
    negatives subtract. Floor at 0."""
    score = 0
    for term in cat.get("keywords", []) + cat.get("phrases", []):
        if cue_match(term, text):
            score += 1
    for pat in cat.get("force_regex", []):
        if re.search(pat, text):
            score += 1
    for term in cat.get("negative", []):
        if cue_match(term, text):
            score -= 1
    return max(0, score)


def is_forced(cat: dict, text: str) -> bool:
    if not any(re.search(pat, text) for pat in cat.get("force_regex", [])):
        return False
    # Negatives can cancel out force signals — only treat as forced if net score > 0.
    return score_category(cat, text) > 0


ACTION_LINE = (
    'ACTION: invoke the "wdym" skill via the Skill tool BEFORE processing '
    "this prompt."
)


def resolve_threshold(ranked, min_score, min_lead):
    """Resolve (verdict, prompt_type, candidates) from ranked (id, score) pairs.

    clear     — winner meets min_score with a min_lead margin, OR carries the
                only signal present (single cue, zero competitors).
    global    — no category scored at all: zero keyword signal is itself a
                deterministic verdict (universal base), mirroring detect.md's
                "weak signals fall back to global" rule.
    ambiguous — competing signals the keyword scorer cannot separate; the
                tied leaders are handed to the LLM as candidates.
    """
    win, win_s = ranked[0]
    run_s = ranked[1][1] if len(ranked) > 1 else 0
    if win_s >= min_score and (win_s - run_s) >= min_lead:
        return "clear", win, []
    if win_s >= 1 and run_s == 0:
        return "clear", win, []
    if win_s == 0:
        return "global", "none", []
    return "ambiguous", "none", [k for k, v in ranked if v == win_s]


def emit_degraded(reason: str, global_flag: bool, raw: str = "") -> int:
    """Hook ran but its config is unusable. Report it so the skill can heal,
    while still honouring --global and never blocking the prompt."""
    log_telemetry({
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "src": "hook",
        "verdict": "degraded",
        "type": "none",
        "passthrough": is_passthrough(raw),
    })
    run_mode, _ = resolve_run_mode()
    lines = [
        '<prompt-detect source="hook" deterministic="true" verdict="degraded">',
        f"reason: {reason}",
        f"global_flag: {str(global_flag).lower()}",
        f"run_mode: {run_mode}",
        "note: deterministic scorer disabled — self-check should heal "
        "refs/categories.json; adjudicate this prompt per refs/detect.md",
        ACTION_LINE,
        "</prompt-detect>",
    ]
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "\n".join(lines),
        }
    }))
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    raw = payload.get("prompt", "")
    if not isinstance(raw, str) or not raw.strip():
        return 0

    # Passthrough prompts get no block — telemetry only. Block present is the
    # binary invoke signal; suppressing it here keeps slash commands and small
    # talk token-free and makes the skill's Step 1 a no-hook fallback only.
    if is_passthrough(raw):
        log_telemetry({
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "src": "hook",
            "verdict": "passthrough",
            "type": "none",
            "passthrough": True,
        })
        return 0

    text = raw.lower()
    global_flag = re.search(r"(?<!\S)--global(?!\S)", text) is not None

    here = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.join(here, "..", "refs", "categories.json")
    try:
        with open(cfg_path, "r", encoding="utf-8") as fh:
            cfg = json.load(fh)
    except FileNotFoundError:
        return emit_degraded("categories.json missing", global_flag, raw)
    except Exception as err:
        return emit_degraded(f"categories.json unparseable ({type(err).__name__})", global_flag, raw)

    cats = cfg.get("categories", [])
    if not isinstance(cats, list) or not cats:
        return emit_degraded("categories.json has no categories", global_flag, raw)

    # Inline mode directives make the run non-deterministic for the hook (the
    # skill persists a pref change) — disable skip and telemetry pre-log.
    inline_directive = re.search(r"(?<!\S)--(flash|comprehensive)(?!\S)", text) is not None

    if not global_flag and not inline_directive and is_well_formed(text, cfg):
        log_telemetry({
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "src": "hook",
            "verdict": "skip",
            "type": "none",
            "passthrough": False,
        })
        return 0

    thr = cfg.get("threshold", {})
    min_score = thr.get("min_score", 2)
    min_lead = thr.get("min_lead", 1)

    scores = {c["id"]: score_category(c, text) for c in cats}
    forced = [c["id"] for c in cats if is_forced(c, text)]

    # Resolve verdict.
    verdict, prompt_type, candidates = "ambiguous", "none", []
    if global_flag:
        verdict, prompt_type = "global", "none"
    elif forced:
        forced_set = set(forced)
        top_forced_score = max(scores[f] for f in forced)
        top_non_forced_score = max(
            (v for k, v in scores.items() if k not in forced_set), default=0
        )
        if top_forced_score >= top_non_forced_score:
            # Forced category leads or ties — forced resolution wins.
            top = sorted(forced, key=lambda i: scores[i], reverse=True)
            if len(top) == 1 or scores[top[0]] > scores[top[1]]:
                verdict, prompt_type = "clear", top[0]
            else:
                candidates = [i for i in top if scores[i] == scores[top[0]]]
        else:
            # A non-forced category outscores the forced one — fall through to
            # normal threshold scoring so the stronger signal wins.
            ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
            verdict, prompt_type, candidates = resolve_threshold(
                ranked, min_score, min_lead
            )
    else:
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        verdict, prompt_type, candidates = resolve_threshold(
            ranked, min_score, min_lead
        )

    # Minimal block: the skill derives mode from verdict+type and reads
    # refs/detect.md only on the ambiguous path, so clear/global carry just the
    # verdict (+ type when clear). scores/candidates ride only on ambiguous,
    # where they seed LLM adjudication. run_mode is the pref pre-resolved;
    # selfcheck appears only on failure; `telemetry: logged` tells the skill
    # its Step 8 line is already written.
    run_mode, pref_wound = resolve_run_mode()
    root = os.path.dirname(here)
    missing = selfcheck(root)
    wounds = missing + ([pref_wound] if pref_wound else [])

    prelog = (run_mode == "flash" and not inline_directive
              and verdict in ("clear", "global"))

    lines = ['<prompt-detect source="hook" deterministic="true">']
    if verdict == "clear":
        lines.append("verdict: clear")
        lines.append(f"prompt_type: {prompt_type}")
    elif verdict == "global":
        lines.append("verdict: global")
    else:  # ambiguous
        score_str = " ".join(f"{k}={v}" for k, v in scores.items())
        lines.append("verdict: ambiguous")
        lines.append(f"scores: {score_str}")
        lines.append(f"candidates: {','.join(candidates) if candidates else 'none'}")
    lines.append(f"run_mode: {run_mode}")
    if wounds:
        lines.append(f"selfcheck: {', '.join(wounds)}")
    if prelog:
        lines.append("telemetry: logged")
    lines.append(ACTION_LINE)
    lines.append("</prompt-detect>")
    context = "\n".join(lines)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log_telemetry({
        "ts": ts,
        "src": "hook",
        "verdict": verdict,
        "type": prompt_type,
        "passthrough": is_passthrough(raw),
    })
    if prelog:
        log_telemetry({
            "ts": ts,
            "src": "skill",
            "type": prompt_type,
            "mode": "global" if verdict == "global" else f"typed:{prompt_type}",
            "run_mode": run_mode,
            "outcome": "run",
        })

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
