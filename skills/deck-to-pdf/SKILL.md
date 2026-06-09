---
name: deck-to-pdf
description: Export an HTML deck, slide page, or long web page to a faithful PDF by screenshotting each section with a real headless browser and stitching the frames into a one-slide-per-page PDF. Use this whenever a user wants a PDF of an HTML presentation/deck/slides/report and the page's own "Print to PDF" / @media print output is broken — wrong pagination, half-empty pages, missing video frames, or lost animated/interactive state. Especially for scroll-snap section decks, video-heavy pages, and canvas/JS-driven visuals.
---

# deck-to-pdf

Turn an HTML page into a PDF that looks **exactly like the browser**, by capturing it rather than re-flowing it through print CSS.

## Why this exists

`@media print` (and Chrome's "Save as PDF") re-lays-out the page for paper. For decks and rich pages that routinely produces: sections split across pages, big empty gaps from flex centering, `<video>` rendered as blank boxes, and scroll-triggered / canvas / hover state missing entirely.

This skill sidesteps all of that: it drives headless Chromium, scrolls to each full-viewport **slide**, lets animations and autoplaying videos settle, takes a retina screenshot, then assembles the screenshots into a clean one-slide-per-page PDF. The PDF is a faithful frame-for-frame capture of what you'd see on screen — video frames and all.

## When to use it

- User says the HTML deck's **PDF / print export looks wrong** (pagination, empty pages, black video boxes).
- You built an HTML **deck / slides / presentation** and need a sendable, printable PDF companion.
- A **video-heavy** or **canvas / JS-animated** page needs a static PDF that still shows the visuals.
- A long scroll page needs to be sliced into PDF pages (`--full-page`).

Not for: ordinary document → PDF where print CSS is fine (use the browser's own print), or generating Word/Excel.

## One-time setup

The helper needs Playwright + Chromium installed **into this skill's directory** (so the script resolves `playwright` from any working directory):

```bash
bash ~/.claude/skills/deck-to-pdf/scripts/setup.sh
```

Run this once. If a run later errors with `Could not load "playwright"`, run setup again.

## Usage

**Always run `--help` first** — treat the script as a black box; don't read its source unless you must customize beyond the flags.

```bash
node ~/.claude/skills/deck-to-pdf/scripts/deck_to_pdf.mjs --help
```

Typical run (one PDF next to the HTML):

```bash
node ~/.claude/skills/deck-to-pdf/scripts/deck_to_pdf.mjs --html /path/to/deck.html
```

Key flags (see `--help` for all):

| flag | purpose | default |
|---|---|---|
| `--html <path>` | input HTML (required) | — |
| `--out <path>` | output PDF | `<html>.pdf` |
| `--selector <css>` | what counts as one slide | `section` |
| `--full-page` | slice a long page by viewport height instead of by selector | off |
| `--width` / `--height` | viewport (slide aspect ratio) | `1600` / `1000` |
| `--scale <n>` | retina factor — crispness vs. file size | `2` |
| `--wait <ms>` | settle time per slide (raise if videos/animations need longer) | `1500` |
| `--hide <css,css>` | overlay selectors to strip (nav dots, hints, progress bars) | `#dots,.hint,#progress` |
| `--keep-frames` | also keep the PNG frames | off |

## How to apply

1. Identify the slide unit. Full-screen `scroll-snap` decks use `<section>` (the default). Other decks may use `.slide`, `.page`, `[data-slide]` — pass it via `--selector`. Long single-flow pages with no slide unit → `--full-page`.
2. Match the aspect ratio to the deck's design (16:10 → `1600×1000`, 16:9 → `1920×1080`).
3. Hide on-screen chrome that shouldn't print — nav dots, keyboard hints, scroll-progress bars — via `--hide` (the default already covers the common `#dots,.hint,#progress`).
4. If a slide's video or entrance animation hasn't finished when captured, raise `--wait` (e.g. `2500`).
5. Report the output path and page count to the user. Mention retina PDFs can be large; suggest `--scale 1` if they need a smaller file.

## Notes & limits

- Designed for **one-slide-per-viewport** decks. A section taller than the viewport gets cropped to the viewport — for such pages use `--full-page`, or make each section fit the viewport.
- Videos are captured as **whatever frame is showing** when the shot fires; it does not embed playable video.
- Output pages are sized to the viewport (`--width × --height`); margins are zero so the capture fills the page edge-to-edge.
- The script also handles assembly internally (via Chromium's `page.pdf` over the captured frames) — no `poppler`/`ffmpeg`/ImageMagick needed.
