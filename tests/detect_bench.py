#!/usr/bin/env python3
"""Regression bench for the wdym deterministic pre-scorer.

Runs representative Claude Code prompts through hooks/prompt-detect.py and
asserts the expected verdict (and type, where clear). Guards category edits
against silently regressing detection. Exit 0 = all pass.

Usage: python3 tests/detect_bench.py

NOTE: invokes the real hook, which appends src:"hook" telemetry lines. The
bench sets CLAUDE_PROJECT_DIR to a temp dir with a .claude/wdym/ so test
lines land in a throwaway telemetry file, never the live one.
"""
import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hooks", "prompt-detect.py")

# (label, prompt, expected_verdict, expected_type_or_None)
# expected_verdict: "clear" | "global" | "ambiguous" | "suppressed" (no block)
CASES = [
    ("code-fix",      "fix the login bug in the auth flow",                          "clear", "code"),
    ("code-explain",  "explain this code and what the reducer does",                 "clear", "code"),
    ("code-refactor", "refactor this component so state lives in the parent",        "clear", "code"),
    ("code-tests",    "the tests are failing after my change, can you investigate",  "clear", "code"),
    ("code-impl",     "implement pagination for the search results endpoint",        "clear", "code"),
    ("code-write",    "write a function to parse dates in python",                   "clear", "code"),
    ("code-error",    "I'm getting TypeError: cannot read properties of undefined when the page loads", "clear", "code"),
    ("code-agentic",  "run the test suite and fix whatever breaks",                  "clear", "code"),
    ("code-review",   "review my changes and tell me if anything looks off",         "clear", "code"),
    ("code-readme",   "update the README to mention the new --flash flag",           "clear", "code"),
    ("question-1",    "what's the difference between let and const?",                "clear", "question"),
    ("question-2",    "why is my app running so slow lately?",                       "clear", "question"),
    ("question-3",    "how does OAuth work under the hood",                          "clear", "question"),
    ("question-4",    "should we use postgres or mongo for this project",            None,    None),  # any deterministic verdict ok
    ("textgen-1",     "draft an email to the team about the outage last night",      "clear", "text-gen"),
    ("textgen-2",     "summarize this document into five bullet points",             "clear", "text-gen"),
    ("textgen-3",     "make this paragraph shorter and less formal",                 "clear", "text-gen"),
    ("mixed-summary", "summarize what this python script does",                      "clear", "code"),
    ("meta-zero",     "recommend improvements to make this whole setup more robust", "global", None),
    ("tie-genuine",   "review my essay and improve the flow of the argument",        "ambiguous", None),
    # Passthrough: no block at all.
    ("pass-slash",    "/wdym --status",                                              "suppressed", None),
    ("pass-short",    "fix it now",                                                  "suppressed", None),
    ("pass-follow",   "thanks, that looks great to me and works",                    "suppressed", None),
]


def run_case(prompt: str, env) -> dict:
    out = subprocess.run(
        ["python3", HOOK], input=json.dumps({"prompt": prompt}),
        capture_output=True, text=True, env=env,
    ).stdout.strip()
    if not out:
        return {"verdict": "suppressed"}
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    parsed = {"action": "ACTION:" in ctx}
    for line in ctx.splitlines():
        for key in ("verdict", "prompt_type", "scores", "candidates"):
            if line.startswith(key + ":"):
                parsed[key] = line.split(":", 1)[1].strip()
    # degraded blocks carry verdict in the tag attribute
    if "verdict" not in parsed and 'verdict="degraded"' in ctx:
        parsed["verdict"] = "degraded"
    return parsed


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, ".claude", "wdym"))
        env = dict(os.environ, CLAUDE_PROJECT_DIR=tmp)
        failures = []
        deterministic = 0
        scored = 0
        print(f"{'label':<14} {'verdict':<11} {'type':<10} {'ok':<4} scores")
        for label, prompt, want_v, want_t in CASES:
            r = run_case(prompt, env)
            v, t = r.get("verdict", "?"), r.get("prompt_type", "-")
            if v != "suppressed":
                scored += 1
                if v in ("clear", "global"):
                    deterministic += 1
                if not r.get("action"):
                    failures.append(f"{label}: block missing ACTION line")
            ok = True
            if want_v is not None and v != want_v:
                ok = False
                failures.append(f"{label}: verdict {v!r} != expected {want_v!r}")
            if want_t is not None and t != want_t:
                ok = False
                failures.append(f"{label}: type {t!r} != expected {want_t!r}")
            if want_v is None and v not in ("clear", "global", "ambiguous"):
                ok = False
                failures.append(f"{label}: unexpected verdict {v!r}")
            print(f"{label:<14} {v:<11} {t:<10} {'✓' if ok else '✗':<4} {r.get('scores', '')}")
        print(f"\ndeterministic (clear/global): {deterministic}/{scored} scored prompts"
              f" ({100 * deterministic // scored if scored else 0}%)")
        if failures:
            print("\nFAILURES:")
            for f in failures:
                print(f"  - {f}")
            return 1
        print("all cases pass")
        return 0


if __name__ == "__main__":
    sys.exit(main())
