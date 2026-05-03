#!/usr/bin/env bash
# link-local.sh — symlink every skill in this repo into ~/.claude/skills/
# so edits land live in Claude Code sessions for development.
#
# Usage:
#   scripts/link-local.sh           # create or refresh symlinks
#   scripts/link-local.sh --unlink  # remove the symlinks created by this script

set -euo pipefail

repo_root=$(cd "$(dirname "$0")/.." && pwd)
skills_dir="$repo_root/skills"
target_dir="$HOME/.claude/skills"

mkdir -p "$target_dir"

unlink_only=false
if [[ "${1:-}" == "--unlink" ]]; then
  unlink_only=true
fi

shopt -s nullglob
for skill_path in "$skills_dir"/*/; do
  name=$(basename "$skill_path")
  link="$target_dir/$name"

  if $unlink_only; then
    if [[ -L "$link" ]]; then
      rm "$link"
      echo "unlinked $link"
    fi
    continue
  fi

  if [[ -e "$link" && ! -L "$link" ]]; then
    echo "SKIP  $link  (exists and is not a symlink — refusing to overwrite)" >&2
    continue
  fi

  ln -sfn "$skill_path" "$link"
  echo "linked $link -> $skill_path"
done
