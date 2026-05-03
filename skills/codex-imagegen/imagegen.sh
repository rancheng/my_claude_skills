#!/usr/bin/env bash
# imagegen.sh — generate an image via `codex exec` (gpt-image-2, "image 2")
# and copy it into the caller's workspace.
#
# Why not just let codex write the file itself?
#   On Linux, codex's bubblewrap sandbox sometimes fails its own cp step with
#   `bwrap: loopback: Failed RTM_NEWADDR: Operation not permitted`. The image
#   is still generated and stashed under ~/.codex/generated_images/<session>/,
#   so we parse that path out of stdout and copy it ourselves. This makes the
#   skill robust regardless of host sandbox config.
#
# Usage:
#   imagegen.sh <output.png> "<prompt>" [reference_image ...]
#
# Examples:
#   imagegen.sh logo.png "minimalist startup logo, blue gradient, vector style"
#   imagegen.sh out.png  "redraw this in watercolor"  ./input.jpg

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <output.png> \"<prompt>\" [reference_image ...]" >&2
  exit 1
fi

out="$1"; shift
prompt="$1"; shift

# Validate refs early so we fail before burning a model call
img_args=()
for ref in "$@"; do
  if [[ ! -f "$ref" ]]; then
    echo "ERROR: reference image not found: $ref" >&2
    exit 1
  fi
  img_args+=(-i "$ref")
done

# Ensure output dir exists
out_dir=$(dirname -- "$out")
mkdir -p "$out_dir"

# --skip-git-repo-check : workspace need not be a git repo
# --sandbox read-only   : we copy the artifact ourselves; codex needs no write
# --ephemeral           : don't pollute session history with one-shot calls
# $imagegen prefix      : forces the built-in image_gen skill (gpt-image-2)
# stdin < /dev/null     : codex exec otherwise reads stdin until EOF and hangs
#                         forever when invoked from a non-TTY parent (Claude
#                         Code's Bash tool, CI, etc.). /dev/null gives immediate
#                         EOF so codex proceeds with the argument prompt only.
log=$(codex exec \
  --skip-git-repo-check \
  --sandbox read-only \
  --ephemeral \
  "${img_args[@]}" \
  "\$imagegen $prompt" < /dev/null 2>&1) || {
    echo "$log" >&2
    echo "ERROR: codex exec failed" >&2
    exit 2
  }

# Pick the last generated_images path codex announced in stdout.
src=$(printf '%s\n' "$log" \
  | grep -oE '/[^ )]*generated_images/[^ )]*\.(png|jpg|jpeg|webp)' \
  | tail -1)

if [[ -z "$src" || ! -f "$src" ]]; then
  echo "$log" >&2
  echo "ERROR: could not locate generated image in codex output" >&2
  exit 3
fi

cp "$src" "$out"
echo "wrote $out  (source: $src)"
