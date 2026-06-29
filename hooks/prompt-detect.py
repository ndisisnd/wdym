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
    if any(low == p or low.startswith(p + " ") for p in FOLLOWUP_PREFIXES):
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
    lines = [
        '<prompt-detect source="hook" deterministic="true" verdict="degraded">',
        f"reason: {reason}",
        f"global_flag: {str(global_flag).lower()}",
        "note: deterministic scorer disabled — self-check should heal "
        "refs/categories.json; adjudicate this prompt per refs/detect.md",
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
            win, win_s = ranked[0]
            run_s = ranked[1][1] if len(ranked) > 1 else 0
            if win_s >= min_score and (win_s - run_s) >= min_lead:
                verdict, prompt_type = "clear", win
            elif win_s >= min_score:
                candidates = [k for k, v in ranked if v == win_s]
    else:
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        win, win_s = ranked[0]
        run_s = ranked[1][1] if len(ranked) > 1 else 0
        if win_s >= min_score and (win_s - run_s) >= min_lead:
            verdict, prompt_type = "clear", win
        elif win_s >= min_score:
            candidates = [k for k, v in ranked if v == win_s]

    score_str = " ".join(f"{k}={v}" for k, v in scores.items())
    lines = [
        '<prompt-detect source="hook" deterministic="true">',
        f"scores: {score_str}",
        f"forced: {','.join(forced) if forced else 'none'}",
        f"global_flag: {str(global_flag).lower()}",
        f"verdict: {verdict}",
    ]
    if verdict in ("clear", "global"):
        mode = "global" if prompt_type == "none" else f"typed:{prompt_type}"
        lines.append(f"prompt_type: {prompt_type}")
        lines.append(f"mode: {mode}")
    else:
        lines.append(f"candidates: {','.join(candidates) if candidates else 'none'}")
        lines.append("note: no clear winner — adjudicate per refs/detect.md")
    lines.append("</prompt-detect>")
    context = "\n".join(lines)

    log_telemetry({
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "src": "hook",
        "verdict": verdict,
        "type": prompt_type,
        "passthrough": is_passthrough(raw),
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
