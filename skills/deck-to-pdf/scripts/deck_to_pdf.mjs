#!/usr/bin/env node
/*
 * deck_to_pdf.mjs — Render an HTML deck/page to a FAITHFUL PDF.
 *
 * Instead of relying on the page's @media print CSS (which usually breaks
 * pagination, drops video frames, and ignores interactive/animated state),
 * this drives a real Chromium: it scrolls to each full-viewport section,
 * lets animations + autoplaying videos settle, screenshots the viewport at
 * retina scale, then stitches the frames into a one-slide-per-page PDF.
 *
 * What you get: exactly what the browser shows — video frames, scroll-reveal
 * animations, hover/active states baked in — with zero print-CSS surprises.
 *
 * Requires `playwright` + the chromium browser. See scripts/setup.sh.
 *
 * Usage:
 *   node deck_to_pdf.mjs --html <file.html> [options]
 *
 * Options:
 *   --html <path>       (required) HTML file to render.
 *   --out <path>        Output PDF. Default: <html basename>.pdf next to the html.
 *   --selector <css>    Element selector for each slide. Default: "section".
 *   --full-page         Ignore --selector; slice the page by viewport height instead.
 *                       Use for long scroll pages that are NOT divided into sections.
 *   --width <px>        Viewport width.  Default: 1600.
 *   --height <px>       Viewport height. Default: 1000.
 *   --scale <n>         deviceScaleFactor (retina). Default: 2.
 *   --wait <ms>         Settle time per slide before the shot. Default: 1500.
 *   --initial-wait <ms> Settle time after first load. Default: 1200.
 *   --hide <css,css>    Comma-list of overlay selectors to hide (nav dots, hints,
 *                       progress bars). Default: "#dots,.hint,#progress".
 *   --css <text>        Extra CSS injected before shooting (advanced).
 *   --keep-frames       Keep the intermediate PNG frames (in a folder next to the PDF).
 *   --frames-only       Only write PNG frames, skip the PDF.
 *   --help
 *
 * Examples:
 *   node deck_to_pdf.mjs --html my_presentation.html
 *   node deck_to_pdf.mjs --html slides.html --selector ".slide" --width 1920 --height 1080
 *   node deck_to_pdf.mjs --html longform.html --full-page --out report.pdf
 */

import { promises as fs } from 'fs';
import path from 'path';
import os from 'os';
import { pathToFileURL } from 'url';

// ---------- tiny arg parser ----------
function parseArgs(argv) {
  const a = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const t = argv[i];
    if (t === '--help' || t === '-h') a.help = true;
    else if (t === '--full-page') a.fullPage = true;
    else if (t === '--keep-frames') a.keepFrames = true;
    else if (t === '--frames-only') a.framesOnly = true;
    else if (t.startsWith('--')) { a[t.slice(2)] = argv[i + 1]; i++; }
    else a._.push(t);
  }
  return a;
}

const HELP = `deck_to_pdf.mjs — render an HTML deck to a faithful PDF (screenshot-per-slide).

  node deck_to_pdf.mjs --html <file.html> [--out out.pdf] [--selector section]
                       [--full-page] [--width 1600] [--height 1000] [--scale 2]
                       [--wait 1500] [--hide "#dots,.hint,#progress"] [--keep-frames]

See the header of this file for the full option list.`;

const args = parseArgs(process.argv.slice(2));
if (args.help || (!args.html && args._.length === 0)) { console.log(HELP); process.exit(args.help ? 0 : 1); }

// ---------- resolve playwright (installed in the skill dir) ----------
let chromium;
try {
  ({ chromium } = await import('playwright'));
} catch (e) {
  console.error('\n✗ Could not load "playwright". Run the one-time setup first:\n' +
    '    bash "' + path.join(path.dirname(new URL(import.meta.url).pathname), 'setup.sh') + '"\n' +
    '  (or: cd into the skill dir, `npm i playwright && npx playwright install chromium`)\n');
  process.exit(2);
}

const htmlPath = path.resolve(args.html || args._[0]);
try { await fs.access(htmlPath); } catch { console.error('✗ HTML not found: ' + htmlPath); process.exit(2); }

const out = path.resolve(args.out || htmlPath.replace(/\.html?$/i, '') + '.pdf');
const selector = args.selector || 'section';
const vw = parseInt(args.width || '1600', 10);
const vh = parseInt(args.height || '1000', 10);
const scale = parseFloat(args.scale || '2');
const wait = parseInt(args.wait || '1500', 10);
const initialWait = parseInt(args['initial-wait'] || '1200', 10);
const hideSel = (args.hide ?? '#dots,.hint,#progress').split(',').map(s => s.trim()).filter(Boolean);
const framesDir = await fs.mkdtemp(path.join(os.tmpdir(), 'deck-frames-'));

console.log(`→ rendering ${path.basename(htmlPath)}  (${vw}×${vh} @${scale}x)`);

const browser = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
const page = await browser.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: scale });
await page.goto(pathToFileURL(htmlPath).href, { waitUntil: 'load' });

// hide nav chrome + inject any extra css
const hideCss = hideSel.length ? hideSel.join(',') + '{display:none !important}' : '';
if (hideCss || args.css) await page.addStyleTag({ content: (hideCss || '') + (args.css || '') });
await page.waitForTimeout(initialWait);

// ---------- collect slides ----------
const frames = [];
async function shoot(i) {
  const f = path.join(framesDir, `slide_${String(i).padStart(3, '0')}.png`);
  await page.screenshot({ path: f });
  frames.push(f);
}

let count = 0;
if (args.fullPage) {
  // slice a long page by viewport height
  const total = await page.evaluate(() => document.documentElement.scrollHeight);
  const pages = Math.max(1, Math.ceil(total / vh));
  for (let i = 0; i < pages; i++) {
    await page.evaluate(y => window.scrollTo(0, y), i * vh);
    await page.waitForTimeout(wait);
    await shoot(i); count++;
  }
} else {
  const els = await page.$$(selector);
  if (!els.length) {
    console.error(`✗ No elements matched selector "${selector}". Try --full-page or a different --selector.`);
    await browser.close(); process.exit(3);
  }
  for (let i = 0; i < els.length; i++) {
    await els[i].scrollIntoViewIfNeeded();
    // nudge any videos in view to play
    await page.evaluate(() => document.querySelectorAll('video').forEach(v => { v.play && v.play().catch(() => {}); }));
    await page.waitForTimeout(wait);
    await shoot(i); count++;
    process.stdout.write(`  · slide ${i + 1}/${els.length}\r`);
  }
}
console.log(`\n→ captured ${count} slide(s)`);

// ---------- assemble PDF (images, one landscape page each) ----------
if (!args.framesOnly) {
  const imgsHtml = '<!doctype html><meta charset=utf-8>' +
    `<style>@page{size:${vw}px ${vh}px;margin:0}html,body{margin:0;background:#000}` +
    `img{width:${vw}px;height:${vh}px;display:block;break-after:page;page-break-after:always}</style><body>` +
    frames.map(f => `<img src="${pathToFileURL(f).href}">`).join('') + '</body>';
  // write to disk and navigate (file:// img loading is far more reliable than setContent)
  const idxFile = path.join(framesDir, '_index.html');
  await fs.writeFile(idxFile, imgsHtml);
  const ip = await browser.newPage();
  await ip.goto(pathToFileURL(idxFile).href, { waitUntil: 'load' });
  // make sure every frame image is fully decoded before printing
  await ip.evaluate(() => Promise.all([...document.images].map(i =>
    i.complete && i.naturalWidth ? null : new Promise(r => { i.onload = i.onerror = r; }))));
  await ip.waitForTimeout(200);
  await ip.pdf({ path: out, width: `${vw}px`, height: `${vh}px`, margin: { top: '0', bottom: '0', left: '0', right: '0' }, printBackground: true, preferCSSPageSize: true });
  console.log(`✓ PDF → ${out}`);
}

await browser.close();

// ---------- frames housekeeping ----------
if (args.keepFrames || args.framesOnly) {
  const dest = out.replace(/\.pdf$/i, '') + '_frames';
  await fs.rm(dest, { recursive: true, force: true });
  await fs.rename(framesDir, dest);
  console.log(`✓ frames → ${dest}`);
} else {
  await fs.rm(framesDir, { recursive: true, force: true });
}
