#!/usr/bin/env python3
"""Token-footprint benchmark for the wdym skill.

Measures what a wdym run actually costs in context tokens:
  1. static footprint — token estimate (bytes/4) of every file the skill loads
     at runtime, split by when it loads (per-invocation / once-per-session /
     conditional);
  2. hook overhead — the real <prompt-detect> block rendered by the hook for
     sample prompts, plus how many corpus prompts it suppresses entirely;
  3. turn model — tool calls per prompt on the happy path (flash, clear
     verdict, healthy install), derived from feature-detecting the hook source
     so the same script benches pre- and post-optimisation trees.

Every extra tool call is one extra API round trip that re-sends the whole
conversation, so `tool_calls` is the strongest efficiency signal even though
its context cost can't be priced statically.

Usage: python3 tests/token_bench.py [--json PATH]
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "hooks", "prompt-detect.py")

PER_INVOCATION = ["SKILL.md"]  # re-injected by every Skill tool call
ONCE_PER_SESSION = [
    "refs/protocol.md",
    "refs/principles/principles-global.md",
    "refs/principles/principles-code.md",
    "refs/principles/principles-question.md",
    "refs/principles/principles-text-gen.md",
]
CONDITIONAL = [  # loaded only on fallback / command / repair paths
    "refs/detect.md",
    "refs/commands.md",
    "refs/help.txt",
    "refs/init.md",
    "refs/manifest.json",
    "refs/heal.md",
]

# Real prompts for hook-block measurement: one per verdict class, then a
# small corpus to estimate the suppression (no-block) rate.
BLOCK_SAMPLES = {
    "clear": "fix the login bug in the auth flow",
    "global": "recommend improvements to make this whole setup more robust",
    "ambiguous": "review my essay and improve the flow of the argument",
}
CORPUS = [
    "fix the login bug in the auth flow",
    "explain this code and what the reducer does",
    "implement pagination for the search results endpoint",
    "write a function to parse dates in python",
    "what's the difference between let and const?",
    "how does OAuth work under the hood",
    "draft an email to the team about the outage last night",
    "summarize this document into five bullet points",
    "make this paragraph shorter and less formal",
    "recommend improvements to make this whole setup more robust",
    # already-well-formed prompts a quality gate should leave alone
    "Write a 200-word overview of common dog breeds for first-time owners.",
    "Review my code and list the top 3 issues by severity, each with a concrete fix.",
    "Summarize the Q2 report below in 5 bullets, ranked by revenue impact.",
    "Explain OAuth token refresh to a non-technical manager in 4 sentences.",
]


def tokens(n_bytes: int) -> int:
    return round(n_bytes / 4)


def file_tokens(rel: str):
    p = os.path.join(ROOT, rel)
    return tokens(os.path.getsize(p)) if os.path.isfile(p) else None


def run_hook(prompt: str, env) -> str:
    """Return the additionalContext block for a prompt, '' if suppressed."""
    out = subprocess.run(
        ["python3", HOOK], input=json.dumps({"prompt": prompt}),
        capture_output=True, text=True, env=env,
    ).stdout.strip()
    if not out:
        return ""
    return json.loads(out)["hookSpecificOutput"]["additionalContext"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="also write the report as JSON to this path")
    args = ap.parse_args()

    src = open(HOOK, encoding="utf-8").read()
    features = {
        # hook resolves pref.json and puts run_mode in the block
        "run_mode_in_block": "run_mode:" in src,
        # hook probes required files; skill skips its ls self-check
        "selfcheck_in_hook": "selfcheck:" in src,
        # hook pre-logs the src:"skill" telemetry line on flash + clear/global
        "telemetry_prelog": "telemetry: logged" in src,
        # hook suppresses the block for already-well-formed prompts
        "well_formed_skip": "well_formed" in src,
    }

    # --- turn model: tool calls on the happy path (flash, clear, healthy) ---
    # Always: 1 Skill invocation. First substantive prompt of a session adds
    # Read(protocol) + Read(principles-global) + Read(principles-<type>).
    first = 1 + 3
    later = 1
    if not features["run_mode_in_block"]:
        first += 1                       # Bash: read pref.json
    if not features["selfcheck_in_hook"]:
        first += 1                       # Bash: ls existence probe
    if not features["telemetry_prelog"]:
        first += 1                       # Bash: telemetry append …
        later += 1                       # … on every run, not just the first

    # --- static footprint ---
    per_inv = {f: file_tokens(f) for f in PER_INVOCATION}
    per_sess = {f: file_tokens(f) for f in ONCE_PER_SESSION}
    cond = {f: file_tokens(f) for f in CONDITIONAL if file_tokens(f) is not None}
    type_files = [v for k, v in per_sess.items() if "principles-" in k
                  and "global" not in k]
    avg_type = round(sum(type_files) / len(type_files)) if type_files else 0
    first_tokens = (sum(per_inv.values())
                    + per_sess["refs/protocol.md"]
                    + per_sess["refs/principles/principles-global.md"]
                    + avg_type)

    # --- hook measurements ---
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, ".claude", "wdym"))
        env = dict(os.environ, CLAUDE_PROJECT_DIR=tmp)
        blocks = {k: tokens(len(run_hook(p, env).encode()))
                  for k, p in BLOCK_SAMPLES.items()}
        suppressed = sum(1 for p in CORPUS if not run_hook(p, env))

    report = {
        "features": features,
        "files": {"per_invocation": per_inv, "once_per_session": per_sess,
                  "conditional": cond},
        "hook_block_tokens": blocks,
        "corpus_suppressed": {"skipped": suppressed, "of": len(CORPUS)},
        "scenario": {
            "tool_calls_first_prompt": first,
            "tool_calls_subsequent_prompt": later,
            "file_tokens_first_prompt": first_tokens,
            "file_tokens_subsequent_prompt": sum(per_inv.values()),
        },
    }

    print(f"features            {' '.join(k for k, v in features.items() if v) or '(baseline)'}")
    print("-- files loaded at runtime (≈tokens) --")
    for group in ("per_invocation", "once_per_session", "conditional"):
        for f, t in report["files"][group].items():
            print(f"  {t:>6}  {group:<17} {f}")
    print("-- hook block (≈tokens per prompt) --")
    for k, t in blocks.items():
        print(f"  {t:>6}  verdict: {k}")
    print(f"-- corpus suppression: {suppressed}/{len(CORPUS)} prompts get no block --")
    print("-- happy-path scenario (flash, clear verdict, healthy install) --")
    s = report["scenario"]
    print(f"  first substantive prompt : {s['tool_calls_first_prompt']} tool calls,"
          f" ≈{s['file_tokens_first_prompt']} file tokens into context")
    print(f"  each later prompt        : {s['tool_calls_subsequent_prompt']} tool calls,"
          f" ≈{s['file_tokens_subsequent_prompt']} file tokens into context")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        print(f"(json → {args.json})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
