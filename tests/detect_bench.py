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

# The block's closing line is user-facing copy on hosts that render
# additionalContext (Codex, per openai/codex#16933) and must stay host-neutral —
# no host-specific filename may reappear in it. Asserted on every emitted block.
SIGNAL_LINE = "signal: wdym classification available — invoke per the wdym auto-invoke contract."
BANNED_IN_BLOCK = ("CLAUDE.md", "AGENTS.md")

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
    ("essay-negate",  "review my essay and improve the flow of the argument",        "clear", "text-gen"),  # code "review" cancelled by "essay" negative
    ("tie-genuine",   "can you explain this error to me please",                     "ambiguous", None),
    # Polysemous code cues must not hijack writing/business prompts:
    ("poly-script-1", "write a script for our product demo video",                   "global", None),
    ("poly-script-2", "help me draft a script for the sales call tomorrow",          "clear", "text-gen"),
    ("poly-compile",  "compile a list of our top competitors and their pricing",     "global", None),
    ("poly-build",    "build an audience for the newsletter over the next quarter",  "global", None),
    ("poly-fix",      "fix the tone of my resume so it sounds less stiff",           "global", None),
    # Passthrough: no block at all.
    ("pass-slash",    "/wdym --status",                                              "suppressed", None),
    ("pass-short",    "fix it now",                                                  "suppressed", None),
    ("pass-follow",   "thanks, that looks great to me and works",                    "suppressed", None),
    # Well-formed skip: already-structured prompts get no block either.
    ("skip-wf-1",     "Write a 200-word overview of common dog breeds for first-time owners.",              "suppressed", None),
    ("skip-wf-2",     "Review my code and list the top 3 issues by severity, each with a concrete fix.",    "suppressed", None),
    ("skip-wf-3",     "Explain OAuth token refresh to a non-technical manager in 4 sentences.",             "suppressed", None),
    # ...but one structure signal alone is not enough (stays scored):
    ("skip-not-1",    "summarize this document into five bullet points",             "clear", "text-gen"),
    # ...and noise cues disable the skip even with structure present:
    ("skip-not-2",    "Please write a 200-word overview of dog breeds for first-time owners, thank you!",   None, None),
]


def run_case(prompt: str, env) -> dict:
    out = subprocess.run(
        ["python3", HOOK], input=json.dumps({"prompt": prompt}),
        capture_output=True, text=True, env=env,
    ).stdout.strip()
    if not out:
        return {"verdict": "suppressed"}
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    parsed = {}
    for line in ctx.splitlines():
        for key in ("verdict", "prompt_type", "scores", "candidates"):
            if line.startswith(key + ":"):
                parsed[key] = line.split(":", 1)[1].strip()
    # degraded blocks carry verdict in the tag attribute
    if "verdict" not in parsed and 'verdict="degraded"' in ctx:
        parsed["verdict"] = "degraded"
    parsed["_ctx"] = ctx
    return parsed


def check_repo_local_resolution() -> list:
    """Launched from a subdirectory, the hook must still find the repo-local
    install rather than falling through to global.

    Only Claude Code sets CLAUDE_PROJECT_DIR; Codex can start anywhere under the
    repo. This runs the hook from a nested subdirectory with that variable unset
    and HOME pointed at an empty throwaway, so the only way to reach the pref is
    the walk up to the repo root."""
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        repo = os.path.join(tmp, "repo")
        sub = os.path.join(repo, "packages", "api", "src")
        wdym_dir = os.path.join(repo, ".claude", "wdym")
        os.makedirs(sub)
        os.makedirs(wdym_dir)
        os.makedirs(os.path.join(repo, ".git"))
        with open(os.path.join(wdym_dir, "pref.json"), "w") as f:
            json.dump({"mode": "flash", "activation": "hook"}, f)
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
        env["HOME"] = os.path.join(tmp, "home")
        os.makedirs(env["HOME"])
        out = subprocess.run(
            ["python3", os.path.abspath(HOOK)],
            input=json.dumps({"prompt": "fix the login bug in the auth flow"}),
            capture_output=True, text=True, env=env, cwd=sub,
        ).stdout.strip()
        if not out:
            failures.append("repo-local: no block emitted from a subdirectory")
            return failures
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        if "run_mode: flash" not in ctx:
            failures.append("repo-local: subdirectory run did not resolve the repo-local pref")
        if not os.path.isfile(os.path.join(wdym_dir, "telemetry.jsonl")):
            failures.append("repo-local: telemetry did not land in the repo-local wdym dir")
    return failures


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        wdym_dir = os.path.join(tmp, ".claude", "wdym")
        os.makedirs(wdym_dir)
        # activation defaults to on-demand, which suppresses every block —
        # the bench tests the scorer, so opt the throwaway install into hook.
        with open(os.path.join(wdym_dir, "pref.json"), "w") as f:
            json.dump({"mode": "comprehensive", "activation": "hook"}, f)
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
            ctx = r.get("_ctx", "")
            if ctx:
                if SIGNAL_LINE not in ctx:
                    ok = False
                    failures.append(f"{label}: block is missing the exact signal line")
                for banned in BANNED_IN_BLOCK:
                    if banned in ctx:
                        ok = False
                        failures.append(
                            f"{label}: block names {banned} — the emitted block must stay host-neutral"
                        )
            print(f"{label:<14} {v:<11} {t:<10} {'✓' if ok else '✗':<4} {r.get('scores', '')}")
        print(f"\ndeterministic (clear/global): {deterministic}/{scored} scored prompts"
              f" ({100 * deterministic // scored if scored else 0}%)")
        scope_failures = check_repo_local_resolution()
        failures.extend(scope_failures)
        print(f"repo-local scope resolution from a subdirectory: "
              f"{'✓' if not scope_failures else '✗'}")
        if failures:
            print("\nFAILURES:")
            for f in failures:
                print(f"  - {f}")
            return 1
        print("all cases pass")
        return 0


if __name__ == "__main__":
    sys.exit(main())
