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

Activation: pref.json's `activation` key is the master switch. `hook` = fire on
every prompt (this scorer runs); `on-demand` = the skill runs only when invoked
via /wdym, and this scorer exits silently even if it is still wired. The pref
outranks the settings wiring so the toggle is instant and the two can never
disagree. `--init` keeps them in sync by wiring/unwiring UserPromptSubmit.

Passthrough prompts (slash command / <=5 words / conversational follow-up) get
NO block at all — only a telemetry line. This makes the contract binary: block
present => substantive prompt => invoke the wdym skill. The block is a neutral
classification signal; the invoke instruction itself lives in the host's own
instruction file (CLAUDE.md on Claude Code, AGENTS.md on Codex) as a trusted,
user-installed contract, so an override-shaped imperative in the block can't be
mistaken for a prompt injection and refused. Block absent => respond normally.

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


def _cwd_walk_dirs():
    """The CWD and its ancestors, nearest first, stopping at the repo root.

    Only Claude Code sets CLAUDE_PROJECT_DIR. Other hosts (Codex) may start the
    session in a subdirectory of the repo, so a repo-local install one or more
    levels up would be missed and the run would silently fall through to the
    global scope. Walking up fixes that without naming a host: stop at the
    directory holding `.git` (the repo root, itself included), and hard-stop at
    $HOME or the filesystem root so an unrelated parent install is never picked
    up. Depth is capped as a cheap guard against pathological trees."""
    dirs = []
    try:
        home = os.path.realpath(os.path.expanduser("~"))
        cur = os.path.realpath(os.getcwd())
    except Exception:
        return dirs
    for _ in range(40):
        dirs.append(cur)
        if os.path.exists(os.path.join(cur, ".git")):
            break
        parent = os.path.dirname(cur)
        if parent == cur or cur == home:
            break
        cur = parent
    return dirs


def state_dirs():
    """wdym state directories in resolution order — nearest scope wins.

    1. $CLAUDE_PROJECT_DIR/.claude/wdym — Claude Code's repo root, when set.
    2. CWD and ancestors up to the repo root, each `.claude/wdym` — the
       host-neutral way to find a repo-local install.
    3. ~/.claude/wdym — the canonical global install, on either host.
    4. $CODEX_HOME/wdym — Codex's config root, when it is set and non-default.

    Order is deduplicated but otherwise preserved, so the same list backs both
    the pref file and the telemetry file and the two can never disagree."""
    dirs = []
    proj = os.environ.get("CLAUDE_PROJECT_DIR")
    if proj:
        dirs.append(os.path.join(proj, ".claude", "wdym"))
    for d in _cwd_walk_dirs():
        dirs.append(os.path.join(d, ".claude", "wdym"))
    dirs.append(os.path.expanduser("~/.claude/wdym"))
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        dirs.append(os.path.join(codex_home, "wdym"))
    ordered = []
    for d in dirs:
        if d not in ordered:
            ordered.append(d)
    return ordered


def telemetry_path():
    """Resolve wdym/telemetry.jsonl at the active install scope (state_dirs
    order: nearest local scope wins, global last). Returns None if no install
    dir exists (the dir is created by --init, never by the hook)."""
    for d in state_dirs():
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


def pref_candidates():
    """Pref file paths in resolution order (same order as telemetry_path):
    the nearest local scope overrides global."""
    return [os.path.join(d, "pref.json") for d in state_dirs()]


def read_pref():
    """Load the first pref.json that exists, local-first. Returns (pref, wound):
    pref is the parsed dict (empty when absent), wound a selfcheck note when a
    pref exists but is unusable (the skill heals it via heal.md)."""
    for p in pref_candidates():
        if not os.path.isfile(p):
            continue
        try:
            with open(p, "r", encoding="utf-8") as fh:
                pref = json.load(fh)
            if not isinstance(pref, dict):
                return {}, "pref invalid"
            return pref, None
        except Exception:
            return {}, "pref unparseable"
    return {}, None


def resolve_activation(pref):
    """Resolve `activation` (`hook` · `on-demand`) — the master switch for
    whether wdym fires on every prompt or only when invoked.

    The pref outranks the settings wiring: an `on-demand` pref silences this
    hook even while it is still wired, so toggling activation never requires
    settings surgery to take effect and the skill's self-check never has to
    referee a disagreement between the two. Absent key => `on-demand`, matching
    the pre-activation default (no pref ever implied an installed hook)."""
    activation = pref.get("activation", "on-demand")
    if activation not in ("hook", "on-demand"):
        return "on-demand", "activation invalid"
    return activation, None


def resolve_run_mode(pref):
    """Resolve `mode` (`comprehensive` · `flash`) — how a run behaves once it
    fires. Defaults to 'comprehensive'; an out-of-enum value is a wound."""
    mode = pref.get("mode")
    if mode is None:
        return "comprehensive", None
    if mode in ("comprehensive", "flash"):
        return mode, None
    return "comprehensive", "pref invalid"


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
    first = re.split(r"[^a-z']+", text.strip(), maxsplit=1)[0]
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


# A neutral signal, not an imperative. The trusted invoke instruction lives in
# the host's own instruction file (CLAUDE.md on Claude Code, AGENTS.md on Codex),
# written by init; the block only reports that a classification is available.
# Override-shaped wording here ('ACTION: ... BEFORE processing this prompt') read
# as a prompt injection through the low-trust hook channel and got refused,
# silently skipping the skill — so the authority moved to that file. The line
# names the contract, not the file, because the filename is host-specific.
#
# Treat this string as user-facing copy: Codex currently renders additionalContext
# as a visible developer message (openai/codex#16933), so the user reads it. One
# tidy status line, no internal plumbing.
ACTION_LINE = (
    "signal: wdym classification available — invoke per the wdym auto-invoke contract."
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
    pref, _ = read_pref()
    run_mode, _ = resolve_run_mode(pref)
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

    # Activation gate — the master switch, checked before any other work. An
    # `on-demand` pref means wdym runs only when invoked (/wdym or an explicit
    # "improve this prompt"), so this hook stays completely silent even while
    # wired: no block, no telemetry, nothing for the skill to heal. Reading the
    # pref here rather than relying on the hook being unwired makes the toggle
    # instant and keeps pref and settings from ever contradicting each other.
    pref, pref_wound = read_pref()
    activation, activation_wound = resolve_activation(pref)
    if activation == "on-demand":
        return 0
    pref_wound = pref_wound or activation_wound

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
    run_mode, mode_wound = resolve_run_mode(pref)
    pref_wound = pref_wound or mode_wound
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
