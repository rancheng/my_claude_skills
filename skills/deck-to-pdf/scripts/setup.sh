#!/usr/bin/env bash
# One-time setup for deck-to-pdf: install Playwright + Chromium INTO the skill dir,
# so `import 'playwright'` resolves no matter what directory the script is run from.
set -e
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SKILL_DIR"
if [ ! -f package.json ]; then printf '{\n  "name": "deck-to-pdf",\n  "private": true,\n  "type": "module"\n}\n' > package.json; fi
echo "→ installing playwright into $SKILL_DIR ..."
npm install playwright@latest
echo "→ installing chromium browser ..."
npx playwright install chromium
echo "✓ setup complete. Try:  node \"$SKILL_DIR/scripts/deck_to_pdf.mjs\" --help"
