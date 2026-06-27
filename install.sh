#!/usr/bin/env bash
#
# install.sh — Installer for the wdym skill.
#
# Copies the skill into your Claude Code skills directory, writes the global
# pref file, and wires the UserPromptSubmit hook into ~/.claude/settings.json
# so the skill fires automatically on every prompt across all projects.
#
# To configure wdym for one specific project only, cd into it and run
# "/wdym --init" (or "wdym --init --local") instead.
#
# Usage:
#   ./install.sh                # install globally (default ~/.claude)
#   SKILL_NAME=wdym ./install.sh
#   CLAUDE_CONFIG_DIR=~/.claude ./install.sh
#
set -euo pipefail

# --- Resolve paths -----------------------------------------------------------
# Source = the directory this script lives in (the skill repo root).
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Target = <claude config>/skills/<skill name>.
CLAUDE_CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
SKILL_NAME="${SKILL_NAME:-wdym}"
SKILLS_DIR="$CLAUDE_CONFIG_DIR/skills"
TARGET_DIR="$SKILLS_DIR/$SKILL_NAME"

info()  { printf '  \033[0;36m•\033[0m %s\n' "$1"; }
ok()    { printf '\033[0;32m✓\033[0m %s\n' "$1"; }
err()   { printf '\033[0;31m✗\033[0m %s\n' "$1" >&2; }

echo "Installing the wdym skill"
echo "  from: $SOURCE_DIR"
echo "  to:   $TARGET_DIR"
echo

# --- Pre-flight checks -------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  err "python3 not found on PATH. The skill's hooks require python3."
  exit 1
fi
info "python3 found: $(command -v python3)"

# The files that constitute the skill. A whitelist keeps dev/local artifacts
# (.git, .claude, .DS_Store, telemetry) out of the install.
REQUIRED=(
  "SKILL.md"
  "pref.json"
  "hooks/prompt-detect.py"
  "hooks/telemetry-stats.py"
  "refs/manifest.json"
  "refs/protocol.md"
  "refs/detect.md"
  "refs/init.md"
  "refs/categories.json"
  "refs/categories.default.json"
  "refs/principles/principles-global.md"
  "refs/principles/principles-code.md"
  "refs/principles/principles-question.md"
  "refs/principles/principles-text-gen.md"
)

missing=0
for f in "${REQUIRED[@]}"; do
  if [[ ! -f "$SOURCE_DIR/$f" ]]; then
    err "missing required file in source: $f"
    missing=1
  fi
done
if [[ "$missing" -ne 0 ]]; then
  err "Source tree is incomplete — aborting without touching the target."
  exit 1
fi
info "all required source files present"

# --- Install -----------------------------------------------------------------
mkdir -p "$TARGET_DIR"

# Copy the curated set: root docs/config, plus the refs/, hooks/, asset/ trees.
# rsync (if present) gives clean excludes; otherwise fall back to cp.
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete \
    --exclude '.git' \
    --exclude '.claude' \
    --exclude '.DS_Store' \
    --exclude 'install.sh' \
    --exclude 'telemetry.jsonl' \
    --exclude 'pref.json' \
    --include 'SKILL.md' \
    --include 'README.md' \
    --include 'CHANGELOG.md' \
    --include 'refs/***' \
    --include 'hooks/***' \
    --include 'asset/***' \
    --exclude '*' \
    "$SOURCE_DIR/" "$TARGET_DIR/"
else
  # Portable fallback.
  cp -f  "$SOURCE_DIR/SKILL.md"   "$TARGET_DIR/"
  [[ -f "$SOURCE_DIR/README.md"    ]] && cp -f "$SOURCE_DIR/README.md"    "$TARGET_DIR/"
  [[ -f "$SOURCE_DIR/CHANGELOG.md" ]] && cp -f "$SOURCE_DIR/CHANGELOG.md" "$TARGET_DIR/"
  for d in refs hooks asset; do
    [[ -d "$SOURCE_DIR/$d" ]] || continue
    rm -rf "${TARGET_DIR:?}/$d"
    cp -R "$SOURCE_DIR/$d" "$TARGET_DIR/$d"
  done
  find "$TARGET_DIR" -name '.DS_Store' -delete 2>/dev/null || true
fi
info "skill files copied"

# Copy pref.json only on a fresh install — preserve any existing user prefs.
if [[ -f "$TARGET_DIR/pref.json" ]]; then
  info "pref.json already exists — keeping existing user preferences"
else
  cp -f "$SOURCE_DIR/pref.json" "$TARGET_DIR/"
  info "pref.json installed (defaults)"
fi

# Hooks are invoked as `python3 "<path>"`, but mark them executable anyway.
chmod +x "$TARGET_DIR/hooks/prompt-detect.py" "$TARGET_DIR/hooks/telemetry-stats.py"
info "hook scripts marked executable"

# Sanity-check the hook parses under the installed python3.
if python3 -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" "$TARGET_DIR/hooks/prompt-detect.py"; then
  info "prompt-detect.py parses cleanly"
else
  err "prompt-detect.py failed to parse — check your python3 install."
  exit 1
fi

# --- Global init: pref.json --------------------------------------------------
GLOBAL_PREF_DIR="$CLAUDE_CONFIG_DIR/wdym"
GLOBAL_PREF_PATH="$GLOBAL_PREF_DIR/pref.json"

mkdir -p "$GLOBAL_PREF_DIR"
if [[ -f "$GLOBAL_PREF_PATH" ]]; then
  info "pref.json already exists (global) — keeping existing preferences"
else
  printf '{"mode":"comprehensive"}\n' > "$GLOBAL_PREF_PATH"
  info "pref.json created at global scope (mode: comprehensive)"
fi

# --- Global init: wire hook into ~/.claude/settings.json ---------------------
SETTINGS_PATH="$CLAUDE_CONFIG_DIR/settings.json"
HOOK_CMD="python3 \"$TARGET_DIR/hooks/prompt-detect.py\""

hook_result=$(python3 - "$SETTINGS_PATH" "$HOOK_CMD" <<'PYEOF'
import sys, json, os

settings_path = sys.argv[1]
hook_cmd = sys.argv[2]

if os.path.exists(settings_path):
    with open(settings_path) as f:
        try:
            settings = json.load(f)
        except json.JSONDecodeError as e:
            print(f"unparseable: {e}", file=sys.stderr)
            sys.exit(1)
else:
    settings = {}

hooks = settings.setdefault("hooks", {})
ups = hooks.setdefault("UserPromptSubmit", [])

for group in ups:
    for h in group.get("hooks", []):
        if h.get("command") == hook_cmd:
            print("already_present")
            sys.exit(0)

ups.append({"hooks": [{"type": "command", "command": hook_cmd}]})

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")

print("added")
PYEOF
)

if [[ "$hook_result" == "added" ]]; then
  info "hook wired into $SETTINGS_PATH (UserPromptSubmit)"
elif [[ "$hook_result" == "already_present" ]]; then
  info "hook already present in $SETTINGS_PATH — no change"
else
  err "could not wire hook — check $SETTINGS_PATH manually"
  exit 1
fi

echo
ok "wdym installed and initialised globally"
echo
echo "The skill fires automatically on every prompt across all projects."
echo "To configure wdym for a specific project only, cd into it and run \"/wdym --init\"."
