# my_claude_skills

A personal marketplace of [Claude Code](https://claude.com/claude-code) skills.

## Skills in this marketplace

| Skill | What it does |
|-------|--------------|
| [`codex-imagegen`](skills/codex-imagegen/) | Generate or edit images via OpenAI's `gpt-image-2` ("image 2") by invoking [`codex exec`](https://developers.openai.com/codex/cli) in headless mode. |
| [`dashscope-videogen`](skills/dashscope-videogen/) | Generate short text-to-video clips via Aliyun DashScope's async video synthesis API (`happyhorse-1.0-t2v` / Wan series). |
| [`deck-to-pdf`](skills/deck-to-pdf/) | Screenshot-per-slide HTML-to-PDF converter using headless Chromium + Playwright. Faithful to browser visuals — handles video frames, scroll-snap decks, canvas/JS-driven pages that break `@media print`. |
| [`svg-animations`](skills/svg-animations/) | Create handcrafted SVG animations — stroke drawing, shape morphing, SMIL, CSS-driven animation, motion paths, gradients, and filters. Based on [supermemoryai/skills/svg-animations](https://github.com/supermemoryai/skills/blob/main/svg-animations/SKILL.md). |

More to come.

## Install

In Claude Code:

```
/plugin marketplace add rancheng/my_claude_skills
/plugin install codex-imagegen@my-claude-skills
/plugin install dashscope-videogen@my-claude-skills
/plugin install deck-to-pdf@my-claude-skills
/plugin install svg-animations@my-claude-skills
```

To pull updates later:

```
/plugin marketplace update my-claude-skills
```

## Manual install (no `/plugin`)

Each skill is a self-contained folder under `skills/`. You can drop one straight into your user-level skills directory:

```bash
git clone https://github.com/rancheng/my_claude_skills.git
cp -r my_claude_skills/skills/codex-imagegen ~/.claude/skills/
chmod +x ~/.claude/skills/codex-imagegen/*.sh
```

## Per-skill prerequisites

- **`codex-imagegen`** — requires the [Codex CLI](https://developers.openai.com/codex/cli) on `PATH` and either `codex login` completed or `OPENAI_API_KEY` exported. Image generation consumes Codex usage credits (3–5× a normal turn).
- **`dashscope-videogen`** — requires a [DashScope API key](https://dashscope.console.aliyun.com/apiKey). On first use Claude will ask you for the key once and persist it to `~/.claude/skill-env/dashscope-videogen.env` (chmod 600, outside any git repo). You can also `export DASHSCOPE_API_KEY=sk-…` in your shell. Video generation consumes Aliyun model credits.

## Repo layout

```
.
├── .claude-plugin/
│   └── marketplace.json     # plugin manifest consumed by Claude Code
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md         # frontmatter (name, description) + instructions
│       └── ...              # any helper scripts the skill calls
├── scripts/
│   └── link-local.sh        # symlink skills into ~/.claude/skills for live dev
├── DEVELOPMENT.md           # how to add a new skill
└── README.md
```

## Adding a new skill

See [DEVELOPMENT.md](DEVELOPMENT.md).

## Credits

- [`svg-animations`](https://github.com/supermemoryai/skills/blob/main/svg-animations/SKILL.md) — adapted from [supermemoryai/skills](https://github.com/supermemoryai/skills) by the Supermemory team.

## License

MIT — see [LICENSE](LICENSE).
