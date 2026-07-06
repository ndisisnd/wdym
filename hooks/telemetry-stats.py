#!/usr/bin/env python3
"""Render the wdym telemetry log as a styled status report.

Invoked by the skill on `/wdym --status` (alias `--stats`), protocol Step 0.
Reads the resolved wdym/telemetry.jsonl (local .claude/wdym/ overrides global
~/.claude/wdym/) and prints an RTK-`gain`-style summary: totals, a transform-rate
meter, and a ranked "By Type" table with impact bars.

Two hybrid streams share the file, tagged by `src`:
  src="hook"  — one deterministic line per submission (every prompt, with a
                passthrough flag and the hook's provisional verdict).
  src="skill" — one line per substantive run the skill actually transformed,
                carrying the final LLM-resolved type/mode and run outcome.

Color is emitted only to a real TTY (and never when NO_COLOR is set), so when the
output is captured by the Bash tool it degrades to clean monochrome Unicode —
no escape-code garbage in the rendered transcript. Dependency-free and
deterministic; bad lines are skipped, never fatal.
"""

import json
import os
import sys

WIDTH = 50  # rule / layout width
TYPES = ("code", "question", "text-gen", "global")


def resolve():
    """Return (telemetry_path, scope_label) at the active install scope, or
    (None, None) if no wdym install dir exists."""
    proj = os.environ.get("CLAUDE_PROJECT_DIR")
    candidates = []
    if proj:
        candidates.append((os.path.join(proj, ".claude", "wdym"), "local"))
    candidates.append((os.path.join(os.getcwd(), ".claude", "wdym"), "local"))
    candidates.append((os.path.expanduser("~/.claude/wdym"), "global"))
    for d, label in candidates:
        if os.path.isdir(d):
            return os.path.join(d, "telemetry.jsonl"), label
    return None, None


def make_palette():
    use = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
    if not use:
        return {k: "" for k in
                ("title", "head", "rule", "label", "val", "bar", "barbg",
                 "warn", "dim", "reset")}
    return {
        "title": "\033[1;36m",   # bold cyan
        "head":  "\033[1;32m",   # bold green
        "rule":  "\033[2;37m",   # dim
        "label": "\033[0;37m",   # light grey
        "val":   "\033[1;37m",   # bold white
        "bar":   "\033[36m",     # cyan
        "barbg": "\033[2;37m",   # dim
        "warn":  "\033[33m",     # yellow
        "dim":   "\033[2;37m",
        "reset": "\033[0m",
    }


def bar(frac, width, c):
    frac = 0.0 if frac < 0 else (1.0 if frac > 1 else frac)
    n = round(frac * width)
    return f"{c['bar']}{'█' * n}{c['barbg']}{'░' * (width - n)}{c['reset']}"


def pct(n, d):
    return (100 * n / d) if d else 0.0


def main() -> int:
    path, scope = resolve()
    c = make_palette()
    if not path or not os.path.isfile(path):
        print("No telemetry recorded yet. "
              "Run some prompts, then try /wdym --status again.")
        return 0

    hook = {"total": 0, "passthrough": 0}
    skill = {"total": 0, "type": {}, "outcome": {}, "global": 0}

    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            src = rec.get("src")
            if src == "hook":
                hook["total"] += 1
                if rec.get("passthrough"):
                    hook["passthrough"] += 1
            elif src == "skill":
                skill["total"] += 1
                mode = rec.get("mode", "")
                bucket = "global" if mode == "global" else rec.get("type", "none")
                skill["type"][bucket] = skill["type"].get(bucket, 0) + 1
                if mode == "global":
                    skill["global"] += 1
                outcome = rec.get("outcome", "?")
                skill["outcome"][outcome] = skill["outcome"].get(outcome, 0) + 1

    total = hook["total"]
    passthrough = hook["passthrough"]
    substantive = total - passthrough
    transformed = skill["total"]
    rate = pct(transformed, substantive) if substantive else 0.0

    rule = c["rule"] + "─" * WIDTH + c["reset"]
    heavy = c["rule"] + "═" * WIDTH + c["reset"]

    def row(label, value, extra=""):
        tail = f"   {c['dim']}{extra}{c['reset']}" if extra else ""
        return (f" {c['label']}{label:<18}{c['reset']}"
                f"{c['val']}{value:>6}{c['reset']}{tail}")

    out = []
    out.append("")
    out.append(f" {c['title']}wdym · prompt telemetry{c['reset']}"
               f"{c['dim']}{('(' + (scope or '—') + ' scope)').rjust(WIDTH - 23)}{c['reset']}")
    out.append(heavy)
    out.append("")
    out.append(row("Total prompts", total))
    out.append(row("Substantive", substantive))
    out.append(row("Transformed", transformed))
    out.append(row("Passthrough", passthrough))
    out.append(row("Pure global runs", skill["global"], "exceptions"))
    out.append(f" {c['label']}{'Transform rate':<18}{c['reset']}"
               f"{bar(rate / 100, 22, c)} {c['val']}{rate:4.0f}%{c['reset']}")
    out.append("")
    out.append(f" {c['head']}By Type{c['reset']}")
    out.append(rule)
    out.append(f"  {c['dim']}{'#':<2} {'Type':<10} {'Count':>5}  "
               f"{'Share':>6}  Impact{c['reset']}")

    counts = {t: skill["type"].get(t, 0) for t in TYPES}
    # include any unexpected buckets (e.g. 'none') so nothing is silently dropped
    for k, v in skill["type"].items():
        if k not in counts:
            counts[k] = v
    top = max(counts.values()) if counts else 0
    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    for i, (t, n) in enumerate(ranked, 1):
        share = pct(n, transformed)
        impact = bar((n / top) if top else 0, 11, c)
        out.append(f"  {c['dim']}{i:<2}{c['reset']} {c['label']}{t:<10}{c['reset']} "
                   f"{c['val']}{n:>5}{c['reset']}  {share:5.1f}%  {impact}")

    o = skill["outcome"]
    outcomes = " · ".join(f"{k} {o[k]}" for k in sorted(o)) or "none"
    out.append("")
    out.append(f" {c['label']}{'Outcomes':<18}{c['reset']}{c['dim']}{outcomes}{c['reset']}")
    out.append("")

    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
