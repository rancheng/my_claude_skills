# Adding and testing a new skill

## 1. Scaffold

```bash
SKILL=my-new-skill
mkdir -p skills/$SKILL
cat > skills/$SKILL/SKILL.md <<'EOF'
---
name: my-new-skill
description: One sentence on what this skill does and the user-request patterns that should trigger it. Be specific about when NOT to trigger too — Claude reads this to decide whether to invoke the skill.
---

# my-new-skill

Instructions for Claude go here. Treat this as a runbook for the model.
EOF
```

Drop any helper scripts the skill calls into the same folder. Keep skills self-contained: a consumer should be able to copy `skills/$SKILL/` and have everything work.

## 2. Wire it into the marketplace manifest

Edit `.claude-plugin/marketplace.json` and add a new entry to `plugins[]`:

```json
{
  "name": "my-new-skill",
  "description": "Same one-liner as in SKILL.md frontmatter.",
  "source": "./",
  "strict": false,
  "skills": ["./skills/my-new-skill"]
}
```

One plugin per skill keeps installs granular — users opt in to what they want.

## 3. Test locally before committing

`scripts/link-local.sh` symlinks every skill in `skills/` into `~/.claude/skills/`. Edits in the repo are picked up live by your Claude Code sessions.

```bash
./scripts/link-local.sh             # create / refresh symlinks
./scripts/link-local.sh --unlink    # remove them
```

Then in a Claude Code session, ask something that should trigger the skill and watch whether Claude invokes it. If it doesn't fire, the description in the frontmatter is the lever — make the trigger conditions more concrete and the negative cases explicit.

## 4. Bump the marketplace version

Edit `.claude-plugin/marketplace.json` → `metadata.version`. Semver:
- `0.x.y` → `0.x.(y+1)` for fixes inside an existing skill.
- `0.x.0` → `0.(x+1).0` for adding a new skill.

## 5. Commit and push

```bash
git add skills/$SKILL .claude-plugin/marketplace.json README.md
git commit -m "Add $SKILL skill"
git push
```

End users pick it up with `/plugin marketplace update my-claude-skills` followed by `/plugin install $SKILL@my-claude-skills`.

## Skill-authoring notes

- **The frontmatter `description` is the trigger.** Claude reads only the description (not the body) when deciding whether to invoke a skill. Pack it with the user phrasings you expect ("create a logo", "make an icon", …) and explicit non-triggers when the skill overlaps with similar tasks.
- **Body is a runbook, not docs.** Write it for the model: ordered steps, failure modes, what to verify before reporting success.
- **Helper scripts > inline instructions.** If the skill needs to run shell commands, put them in a script in the skill folder and have the SKILL.md tell Claude to invoke it. Easier to test, easier to debug.
- **Verify the result.** The skill's runbook should always end with an explicit verification step (read the file, run the test, render the artifact) before claiming success.
