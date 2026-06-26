#!/usr/bin/env python3
"""UserPromptSubmit pre-scorer for the prompt-engineer (wdym) skill.

Deterministic keyword/regex classifier. Reads the submitted prompt, scores it
against refs/categories.json, and injects a <prompt-detect> block as additional
context. The skill's detect protocol (refs/detect.md, Step 2) consumes this:
trust the verdict when `clear`, adjudicate among `candidates` when `ambiguous`.

Contract: never block or mutate the prompt. Any failure exits 0 with no output,
so a broken scorer degrades to pure-LLM detection rather than dropping the prompt.
"""

import json
import os
import re
import sys


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
    return any(re.search(pat, text) for pat in cat.get("force_regex", []))


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
    except Exception:
        return 0

    cats = cfg.get("categories", [])
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
        top = sorted(forced, key=lambda i: scores[i], reverse=True)
        if len(top) == 1 or scores[top[0]] > scores[top[1]]:
            verdict, prompt_type = "clear", top[0]
        else:
            candidates = [i for i in top if scores[i] == scores[top[0]]]
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

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
