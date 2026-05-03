---
name: dashscope-videogen
description: Generate short text-to-video clips via Aliyun DashScope's async video synthesis API (e.g. `happyhorse-1.0-t2v`, Wan series). Trigger when the user asks to create, generate, or make a video / animation / clip / 视频 from a text description — and they have not specified a different generator (Sora, Runway, Pika, Kling, Luma, etc.). Also trigger when the user mentions DashScope, 通义万相, 阿里视频生成, or `happyhorse` / Wan video models.
---

# dashscope-videogen

Generates short videos from a text prompt using Aliyun DashScope's async video synthesis endpoint. The bundled `videogen.py` owns submission, polling, key resolution, and download — Claude just chooses parameters and invokes it.

## Key management — do this first if invocation fails

The script needs `DASHSCOPE_API_KEY`. Resolution order:

1. `DASHSCOPE_API_KEY` exported in the current shell.
2. `~/.claude/skill-env/dashscope-videogen.env` (the persistent local file the skill writes — outside any source tree, chmod 600).

If neither is set, the script exits with code 2 and a clear message. **Never** hard-code, log, or commit a key. Never write the key into a file inside this skill folder or any other git-tracked path — only `set-key` (which writes to `~/.claude/skill-env/`) is acceptable.

### When the user has not yet provided a key

1. Run `python3 ~/.claude/skills/dashscope-videogen/videogen.py check-key`.
2. If it reports `MISSING`, ask the user once, in plain language, for their DashScope API key (link them to <https://dashscope.console.aliyun.com/apiKey> if they don't know where to find it).
3. When they paste it, persist it:

   ```bash
   python3 ~/.claude/skills/dashscope-videogen/videogen.py set-key sk-XXXXXXXX
   ```

   The script writes to `~/.claude/skill-env/dashscope-videogen.env` (chmod 600) and prints a masked confirmation. Future Claude sessions reuse it automatically.
4. Then proceed with the actual generation request.

If the user prefers not to persist, they can `export DASHSCOPE_API_KEY=...` in their shell instead — the script picks up the env var first.

## How to invoke (the happy path)

```bash
python3 ~/.claude/skills/dashscope-videogen/videogen.py generate <output.mp4> "<prompt>" \
  [--model happyhorse-1.0-t2v] \
  [--resolution 720P] \
  [--ratio 16:9] \
  [--duration 5]
```

- `<output.mp4>` — absolute or workspace-relative path. Default to the current working directory; do not write to `/tmp` unless the user asks.
- `<prompt>` — pass the user's prompt verbatim unless they asked for refinement. The API accepts Chinese and English.
- Optional flags map 1:1 to the DashScope `parameters` block. Defaults match the most common request (720P, 16:9, 5s, `happyhorse-1.0-t2v`).

The script:
1. Submits the async job with `X-DashScope-Async: enable`.
2. Prints the `task_id` and a one-liner showing how to `resume` if polling is interrupted.
3. Polls `/api/v1/tasks/{task_id}` every 10s. Status transitions: `PENDING` → `RUNNING` → `SUCCEEDED` (typical 60–120s for a 5s/720P clip).
4. Downloads the resulting mp4 to `<output.mp4>`.

Allow up to ~5 minutes wall-clock. Don't kill it early.

## Standard workflow

1. **Verify the key is configured** if you have any doubt — `videogen.py check-key`. Skip this if you've just used the skill in this session.
2. **Pick a sensible filename** in the user's working directory (e.g. `video.mp4`, `cardboard_city.mp4`). Don't invent random names.
3. **Run `videogen.py generate`** via Bash. The script streams progress lines (`task_status=RUNNING`, then `SUCCEEDED`).
4. **Verify the output** — confirm the file exists and report its size (e.g. `ls -lh <output.mp4>`). The video URL the API returns is presigned and short-lived; the local mp4 is the deliverable.
5. **Report briefly:** filename, file size, duration/resolution actually requested, and the prompt used. Do not embed the presigned `video_url` in your reply — it leaks via screenshots and expires anyway.

## Resuming an interrupted job

If the polling step is interrupted (network drop, user Ctrl-C, timeout) but you still have the `task_id` printed at submission time:

```bash
python3 ~/.claude/skills/dashscope-videogen/videogen.py resume <task_id> <output.mp4>
```

This skips submission and goes straight to poll-then-download. Useful if the user comes back later — DashScope retains finished tasks for a while.

## Failure modes

- **`HTTP 401` / `InvalidApiKey`** — the saved key is wrong or revoked. Run `set-key` again with a fresh key. Do not retry silently.
- **`HTTP 429` / throttling** — back off and tell the user; do not auto-retry hard.
- **`task_status=FAILED`** — the response body usually contains `code` / `message` (e.g. `DataInspectionFailed` for prompt content). Surface those fields verbatim to the user and adjust the prompt; do not try to bypass content policy.
- **Polling timeout (default 30 min)** — for unusually long jobs, the job is probably still running server-side. Re-run with `resume <task_id>` to keep polling without resubmitting.
- **`ModuleNotFoundError`** — should not happen, the script uses only the Python stdlib. If it does, check the user has Python 3.8+.

## What this skill does NOT do

- **No image-to-video / video-to-video.** Only the text-to-video synthesis endpoint is wired up. If the user wants i2v or extend, say so and either propose extending this skill or fall back to writing a one-shot Python call.
- **No Stable Diffusion / Sora / Pika.** This is DashScope-specific. If the user explicitly asks for another provider, do not use this skill.
- **No watermark removal.** The default `happyhorse-1.0-t2v` returns a watermarked mp4 (`..._watermark.mp4`). That's a model-side decision — mention it to the user if relevant; do not attempt to strip it.
- **No key sharing.** The key is per-user. Never echo the key back in chat, never put it in a commit, never store it inside the skill directory or any directory that could be a git repo.
