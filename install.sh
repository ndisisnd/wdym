#!/usr/bin/env bash
#
# install.sh — Installer for the wdym skill.
#
# Fetches the skill as a tarball, unpacks it into a Claude Code skills
# directory, writes the pref file, and wires the UserPromptSubmit hook so the
# skill fires automatically on every prompt.
#
# Local is the default: everything lands under ./.claude/ and wdym fires only
# in this project. Pass --global to install under ~/.claude/ instead, where it
# fires across every project.
#
# The installer never needs the wdym repo on disk — it pulls a tarball into a
# temp dir, installs from there, and cleans up. Run it from the project you
# want wdym in, not from a clone of wdym.
#
# Usage:
#   ./install.sh                       # local install into ./.claude
#   ./install.sh --global              # global install into ~/.claude
#   ./install.sh --dir path/to/project # local install into another project
#   ./install.sh --tarball ./wdym.tar.gz
#   ./install.sh --tarball https://example.com/wdym.tar.gz
#
# Or without cloning anything:
#   curl -fsSL https://raw.githubusercontent.com/ndisisnd/wdym/main/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/ndisisnd/wdym/main/install.sh | bash -s -- --global
#
# Environment:
#   WDYM_TARBALL       default tarball URL or local .tar.gz path
#   CLAUDE_CONFIG_DIR  global config root (default ~/.claude)
#   SKILL_NAME         installed skill directory name (default wdym)
#
set -euo pipefail

DEFAULT_TARBALL="https://github.com/ndisisnd/wdym/archive/refs/heads/main.tar.gz"

info()  { printf '  \033[0;36m•\033[0m %s\n' "$1"; }
ok()    { printf '\033[0;32m✓\033[0m %s\n' "$1"; }
err()   { printf '\033[0;31m✗\033[0m %s\n' "$1" >&2; }

usage() {
  # Piped into bash (curl | bash) there is no script file to read the header from.
  if [[ -r "${BASH_SOURCE[0]:-}" ]]; then
    sed -n '3,32p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  else
    printf 'install.sh [--local|--global] [--dir <project>] [--tarball <url|path>] [--force]\n'
  fi
}

# --- Parse arguments ---------------------------------------------------------
SCOPE="local"
PROJECT_DIR=""
TARBALL="${WDYM_TARBALL:-$DEFAULT_TARBALL}"
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    -g|--global) SCOPE="global"; shift ;;
    -l|--local)  SCOPE="local";  shift ;;
    --dir)       PROJECT_DIR="${2:-}"; [[ -n "$PROJECT_DIR" ]] || { err "--dir needs a path"; exit 1; }; shift 2 ;;
    --tarball)   TARBALL="${2:-}";     [[ -n "$TARBALL"     ]] || { err "--tarball needs a URL or path"; exit 1; }; shift 2 ;;
    --force)     FORCE=1; shift ;;
    -h|--help)   usage; exit 0 ;;
    *)           err "unknown argument: $1"; echo; usage; exit 1 ;;
  esac
done

# --- Resolve target paths ----------------------------------------------------
# Local  → <project>/.claude          + settings.local.json  (personal, uncommitted)
# Global → $CLAUDE_CONFIG_DIR (~/.claude) + settings.json    (all projects)
SKILL_NAME="${SKILL_NAME:-wdym}"

if [[ "$SCOPE" == "global" ]]; then
  BASE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
  SETTINGS_PATH="$BASE_DIR/settings.json"
else
  PROJECT_DIR="${PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$PWD}}"
  [[ -d "$PROJECT_DIR" ]] || { err "no such directory: $PROJECT_DIR"; exit 1; }
  PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"
  BASE_DIR="$PROJECT_DIR/.claude"
  SETTINGS_PATH="$BASE_DIR/settings.local.json"

  # A local install into the wdym repo itself would nest the skill inside its
  # own source tree (wdym/.claude/skills/wdym). Almost never what you want.
  if [[ "$FORCE" -ne 1 && -f "$PROJECT_DIR/SKILL.md" && -f "$PROJECT_DIR/hooks/prompt-detect.py" ]]; then
    err "$PROJECT_DIR looks like the wdym source repo — installing here would nest wdym inside itself."
    err "cd into the project you want wdym in, or pass --dir <project>, --global, or --force."
    exit 1
  fi
fi

TARGET_DIR="$BASE_DIR/skills/$SKILL_NAME"
PREF_PATH="$BASE_DIR/wdym/pref.json"

echo "Installing the wdym skill ($SCOPE scope)"
echo "  from: $TARBALL"
echo "  to:   $TARGET_DIR"
echo

# --- Pre-flight checks -------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  err "python3 not found on PATH. The skill's hooks require python3."
  exit 1
fi
info "python3 found: $(command -v python3)"

command -v tar >/dev/null 2>&1 || { err "tar not found on PATH."; exit 1; }

# --- Fetch and unpack the tarball --------------------------------------------
STAGE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/wdym-install.XXXXXX")"
cleanup() { rm -rf "$STAGE_DIR"; }
trap cleanup EXIT

# --strip-components=1 drops the archive's top-level directory (e.g. wdym-main/),
# so the skill files land directly in $STAGE_DIR.
if [[ -f "$TARBALL" ]]; then
  tar -xzf "$TARBALL" --strip-components=1 -C "$STAGE_DIR"
  info "tarball unpacked from local file"
else
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$TARBALL" | tar -xzf - --strip-components=1 -C "$STAGE_DIR"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- "$TARBALL" | tar -xzf - --strip-components=1 -C "$STAGE_DIR"
  else
    err "neither curl nor wget found on PATH — cannot download $TARBALL"
    exit 1
  fi
  info "tarball downloaded and unpacked"
fi

# The files that constitute the skill. Verifying them against the unpacked
# tarball catches a truncated download before anything touches the target.
REQUIRED=(
  "SKILL.md"
  "hooks/prompt-detect.py"
  "hooks/telemetry-stats.py"
  "refs/manifest.json"
  "refs/protocol.md"
  "refs/commands.md"
  "refs/help.txt"
  "refs/detect.md"
  "refs/init.md"
  "refs/authoring.md"
  "refs/categories.json"
  "refs/categories.default.json"
  "refs/principles/principles-global.md"
  "refs/principles/principles-code.md"
  "refs/principles/principles-question.md"
  "refs/principles/principles-text-gen.md"
)

missing=0
for f in "${REQUIRED[@]}"; do
  if [[ ! -f "$STAGE_DIR/$f" ]]; then
    err "missing required file in tarball: $f"
    missing=1
  fi
done
if [[ "$missing" -ne 0 ]]; then
  err "Tarball is incomplete — aborting without touching the target."
  exit 1
fi
info "all required files present in tarball"

# --- Install -----------------------------------------------------------------
# A dev install symlinks the skill dir straight at a working tree; replacing it
# would clobber the developer's checkout. Keep the symlink, skip the unpack.
if [[ -L "$TARGET_DIR" ]]; then
  info "target is a symlink (dev install) — leaving it in place; skipping copy"
else
  mkdir -p "$TARGET_DIR"

  # Curated set only: root docs, plus the refs/, hooks/, asset/ trees. Dev and
  # repo-only artifacts (install.sh, tests/, .github/, pref.json) stay behind.
  cp -f "$STAGE_DIR/SKILL.md" "$TARGET_DIR/"
  for f in README.md CHANGELOG.md; do
    [[ -f "$STAGE_DIR/$f" ]] && cp -f "$STAGE_DIR/$f" "$TARGET_DIR/"
  done
  for d in refs hooks asset; do
    [[ -d "$STAGE_DIR/$d" ]] || continue
    rm -rf "${TARGET_DIR:?}/$d"
    cp -R "$STAGE_DIR/$d" "$TARGET_DIR/$d"
  done
  find "$TARGET_DIR" -name '.DS_Store' -delete 2>/dev/null || true
  info "skill files installed"
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

# --- Init: pref.json ---------------------------------------------------------
mkdir -p "$(dirname "$PREF_PATH")"
if [[ -f "$PREF_PATH" ]]; then
  info "pref.json already exists ($SCOPE) — keeping existing preferences"
else
  printf '{"mode":"comprehensive"}\n' > "$PREF_PATH"
  info "pref.json created at $SCOPE scope (mode: comprehensive)"
fi

# --- Init: wire the UserPromptSubmit hook ------------------------------------
# The command carries the absolute skill path so it resolves from any cwd.
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

os.makedirs(os.path.dirname(settings_path) or ".", exist_ok=True)
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
ok "wdym installed and initialised ($SCOPE scope)"
echo
if [[ "$SCOPE" == "global" ]]; then
  echo "The skill fires automatically on every prompt across all projects."
  echo "To scope it to one project instead, cd into it and run \"./install.sh\" (or \"/wdym --init --local\")."
else
  echo "The skill fires automatically on every prompt in $PROJECT_DIR."
  echo "To install it for every project, run \"./install.sh --global\"."
  echo "Local settings live in .claude/settings.local.json — keep it out of version control."
fi
