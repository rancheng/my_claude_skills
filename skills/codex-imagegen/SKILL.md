---
name: codex-imagegen
description: Generate or edit images by invoking OpenAI's gpt-image-2 ("image 2") through headless `codex exec`. Trigger when the user asks to create, generate, draw, design, or edit an image, logo, icon, illustration, banner, sprite sheet, placeholder art, or any visual asset — and they have not specified a different generator (Stable Diffusion, Midjourney, DALL·E API directly, etc.). Also use when the user wants to transform or extend a reference image they have provided locally.
---

# codex-imagegen

Generates images via the **`gpt-image-2`** model (the "image 2" model) by invoking the Codex CLI in non-interactive mode. The Codex CLI's built-in `image_gen` skill handles the actual model call; this skill is the bridge that lets Claude Code drive it headlessly and place the result inside the user's workspace.

## Prerequisites (verify only if invocation fails)

- `codex` is on PATH (`which codex`).
- The user is logged in (`~/.codex/auth.json` exists) **or** `OPENAI_API_KEY` is set in the environment.
- Image generation consumes Codex usage credits (3–5× faster than a text turn). Mention this only if the user expresses cost concerns.

## How to invoke

Run the bundled helper script. It owns all the flags, the `$imagegen` prefix, the stdout-parse, and the bwrap-sandbox workaround.

```bash
~/.claude/skills/codex-imagegen/imagegen.sh <output.png> "<prompt>" [reference_image ...]
```

- `<output.png>` — absolute or workspace-relative path where the final PNG should land.
- `<prompt>` — the image description. Be specific about subject, style, composition, palette, and background. The script auto-prepends `$imagegen` so Codex routes to the built-in image skill.
- `[reference_image ...]` — zero or more local image files to attach as references (passed through `codex exec -i`). Use these when the user wants to transform, restyle, or extend an existing asset.

The script writes the final file to `<output.png>` and prints `wrote <output.png>  (source: <codex-cache-path>)` on success.

## Standard workflow

1. **Clarify the prompt only if it is genuinely ambiguous.** A one-line user request like "make me a logo" warrants a quick check on style / palette / use case; "minimalist flat icon of a robot painter" does not. Don't over-question.
2. **Pick a sensible output filename** in the current working directory (e.g. `logo.png`, `hero.png`). Don't put it in `/tmp` unless the user asks.
3. **Run the script** via Bash. Allow up to ~120s for generation.
4. **Display the result.** After success, use the `Read` tool on the output PNG so the image renders inline for the user. This is the verification step — never claim success without doing it.
5. **Report briefly:** filename, dimensions (from `file <out>` if useful), and the prompt actually used. Skip filler.

## Editing / reference-image flow

When the user provides a source image and wants it modified:

```bash
~/.claude/skills/codex-imagegen/imagegen.sh out.png \
  "Redraw this scene in watercolor, soft pastel palette, preserve composition" \
  ./input.jpg
```

Codex will receive the reference via `-i` and the prompt should describe the *transformation*, not redescribe the source.

## Failure modes & recovery

- **`bwrap: Failed RTM_NEWADDR: Operation not permitted`** — Linux sandbox blocks codex's own copy step. The helper already works around this by parsing the source path from stdout and copying it itself, so this should not surface to the user. If it does, the image was still generated; rerun the script or grep `~/.codex/generated_images/` for the most recent file.
- **`could not locate generated image in codex output`** — codex exec failed before producing a file. Re-read the captured stderr (the script prints the full log on failure) to diagnose: auth issues, rate limits, content-policy refusals.
- **Wrong content / refusal** — adjust the prompt and rerun. Don't try to bypass content policy.

## What this skill does NOT do

- It does not call the OpenAI Images API directly with `curl` / the SDK. If the user explicitly wants the raw API (e.g. for batch generation, custom params not exposed by Codex), say so and write a small Python/Node script instead.
- It does not run inside the Codex container — it runs `codex exec` from the user's shell.
- It does not manage Codex auth. If `auth.json` is missing and `OPENAI_API_KEY` is unset, tell the user to run `codex login` themselves; do not attempt it for them (it's interactive).
