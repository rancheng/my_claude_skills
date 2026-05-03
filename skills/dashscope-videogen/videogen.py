#!/usr/bin/env python3
"""DashScope video generation skill.

Submits a text-to-video job to Aliyun DashScope's async video synthesis endpoint,
polls for completion, and downloads the resulting mp4.

Subcommands:
  generate <output.mp4> <prompt> [--model ...] [--resolution 720P] [--ratio 16:9] [--duration 5]
  resume   <task_id> <output.mp4>      # re-poll an existing task and download
  set-key  [<key>] [--stdin]           # persist DASHSCOPE_API_KEY to local skill env file
  check-key                            # report key source (env / file / missing)

Key resolution order:
  1. DASHSCOPE_API_KEY environment variable
  2. ~/.claude/skill-env/dashscope-videogen.env

The local env file is created with chmod 600 inside chmod 700 ~/.claude/skill-env/
and lives outside any source-controlled directory, so the key never reaches git.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


SKILL_NAME = "dashscope-videogen"
ENV_KEY = "DASHSCOPE_API_KEY"
KEY_FILE = Path.home() / ".claude" / "skill-env" / f"{SKILL_NAME}.env"

SUBMIT_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis"
QUERY_URL_TMPL = "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"


# ---------- key management ----------

def load_key_file():
    if not KEY_FILE.is_file():
        return None
    for raw in KEY_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == ENV_KEY:
            return v.strip().strip('"').strip("'")
    return None


def get_key():
    return os.environ.get(ENV_KEY) or load_key_file()


def require_key():
    key = get_key()
    if not key:
        script = Path(__file__).name
        print(
            f"ERROR: {ENV_KEY} not configured.\n"
            f"  Option A (current shell only):  export {ENV_KEY}=sk-...\n"
            f"  Option B (persist for all future runs of this skill):\n"
            f"    python3 {script} set-key sk-...\n"
            f"  Stored at: {KEY_FILE}",
            file=sys.stderr,
        )
        sys.exit(2)
    return key


def cmd_set_key(args):
    if args.stdin:
        key = sys.stdin.readline().strip()
    elif args.key:
        key = args.key.strip()
    else:
        print("ERROR: provide the key as an argument or use --stdin", file=sys.stderr)
        sys.exit(1)

    if not key:
        print("ERROR: empty key", file=sys.stderr)
        sys.exit(1)

    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        KEY_FILE.parent.chmod(0o700)
    except PermissionError:
        pass

    lines = []
    replaced = False
    if KEY_FILE.is_file():
        for raw in KEY_FILE.read_text(encoding="utf-8").splitlines():
            stripped = raw.strip()
            if stripped.startswith(f"{ENV_KEY}=") or stripped.startswith(f"{ENV_KEY} ="):
                lines.append(f"{ENV_KEY}={key}")
                replaced = True
            else:
                lines.append(raw)
    if not replaced:
        lines.append(f"{ENV_KEY}={key}")

    KEY_FILE.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    KEY_FILE.chmod(0o600)
    masked = key[:6] + "…" + key[-4:] if len(key) > 12 else "***"
    print(f"Saved {ENV_KEY}={masked} to {KEY_FILE} (chmod 600).")


def cmd_check_key(args):
    if os.environ.get(ENV_KEY):
        print(f"OK  {ENV_KEY} set in environment.")
        return
    if load_key_file():
        print(f"OK  {ENV_KEY} loaded from {KEY_FILE}")
        return
    print(f"MISSING  {ENV_KEY} not set in env and not present in {KEY_FILE}")
    sys.exit(1)


# ---------- HTTP ----------

def _request(url, method, headers, payload=None, timeout=60):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} {e.reason}: {body}") from None


def submit(key, prompt, model, resolution, ratio, duration):
    headers = {
        "X-DashScope-Async": "enable",
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "input": {"prompt": prompt},
        "parameters": {
            "resolution": resolution,
            "ratio": ratio,
            "duration": duration,
        },
    }
    resp = _request(SUBMIT_URL, "POST", headers, payload)
    task_id = (resp.get("output") or {}).get("task_id")
    if not task_id:
        raise RuntimeError(f"No task_id in response: {resp}")
    return task_id


def query(key, task_id):
    headers = {"Authorization": f"Bearer {key}"}
    return _request(QUERY_URL_TMPL.format(task_id=task_id), "GET", headers)


def poll(key, task_id, poll_interval, timeout):
    start = time.time()
    while True:
        resp = query(key, task_id)
        out = resp.get("output") or {}
        status = out.get("task_status")
        elapsed = int(time.time() - start)
        print(f"[{elapsed}s] task_status={status}", flush=True)
        if status == "SUCCEEDED":
            return resp
        if status in ("FAILED", "CANCELED", "UNKNOWN"):
            raise RuntimeError(f"Task ended with status={status}: {resp}")
        if time.time() - start > timeout:
            raise TimeoutError(f"Polling timed out after {timeout}s, last status={status}")
        time.sleep(poll_interval)


def download(url, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading -> {out_path}", flush=True)
    urllib.request.urlretrieve(url, str(out_path))
    print(f"wrote {out_path}", flush=True)


# ---------- commands ----------

def cmd_generate(args):
    key = require_key()
    print(f"Prompt: {args.prompt}", flush=True)
    task_id = submit(
        key,
        args.prompt,
        args.model,
        args.resolution,
        args.ratio,
        args.duration,
    )
    print(f"Submitted task_id={task_id}", flush=True)
    print(f"  (resume with: python3 {Path(__file__).name} resume {task_id} {args.output})", flush=True)
    result = poll(key, task_id, args.poll_interval, args.timeout)
    video_url = (result.get("output") or {}).get("video_url")
    if not video_url:
        raise RuntimeError(f"No video_url in result: {result}")
    print(f"video_url={video_url}", flush=True)
    download(video_url, args.output)


def cmd_resume(args):
    key = require_key()
    print(f"Resuming task_id={args.task_id}", flush=True)
    result = poll(key, args.task_id, args.poll_interval, args.timeout)
    video_url = (result.get("output") or {}).get("video_url")
    if not video_url:
        raise RuntimeError(f"No video_url in result: {result}")
    print(f"video_url={video_url}", flush=True)
    download(video_url, args.output)


def build_parser():
    p = argparse.ArgumentParser(description="DashScope video generation skill.")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="Submit prompt, poll, download mp4.")
    g.add_argument("output", help="Output mp4 path.")
    g.add_argument("prompt", help="Text prompt for the video.")
    g.add_argument("--model", default="happyhorse-1.0-t2v")
    g.add_argument("--resolution", default="720P", help="e.g. 480P / 720P / 1080P")
    g.add_argument("--ratio", default="16:9", help="e.g. 16:9 / 9:16 / 1:1")
    g.add_argument("--duration", type=int, default=5, help="Seconds.")
    g.add_argument("--poll-interval", type=int, default=10)
    g.add_argument("--timeout", type=int, default=1800)
    g.set_defaults(func=cmd_generate)

    r = sub.add_parser("resume", help="Re-poll an existing task_id and download.")
    r.add_argument("task_id")
    r.add_argument("output")
    r.add_argument("--poll-interval", type=int, default=10)
    r.add_argument("--timeout", type=int, default=1800)
    r.set_defaults(func=cmd_resume)

    s = sub.add_parser("set-key", help="Persist DASHSCOPE_API_KEY to local skill env file.")
    s.add_argument("key", nargs="?", default=None)
    s.add_argument("--stdin", action="store_true", help="Read the key from one line of stdin.")
    s.set_defaults(func=cmd_set_key)

    c = sub.add_parser("check-key", help="Report whether the key is configured.")
    c.set_defaults(func=cmd_check_key)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
