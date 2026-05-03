# my_claude_skills

A personal marketplace of [Claude Code](https://claude.com/claude-code) skills.

## Skills in this marketplace

| Skill | What it does |
|-------|--------------|
| [`codex-imagegen`](skills/codex-imagegen/) | Generate or edit images via OpenAI's `gpt-image-2` ("image 2") by invoking [`codex exec`](https://developers.openai.com/codex/cli) in headless mode. |

More to come.

## Install

In Claude Code:

```
/plugin marketplace add rancheng/my_claude_skills
/plugin install codex-imagegen@my-claude-skills
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

## License

MIT — see [LICENSE](LICENSE).
