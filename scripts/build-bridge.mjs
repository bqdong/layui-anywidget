#!/usr/bin/env node
// Build static/layui-bridge.js from static/src/bridge.js and the vendored
// layui assets.  The bridge must be a single self-contained ES module because
// anywidget executes `_esm` from a Blob URL, where relative imports cannot be
// resolved.  Layui's UMD source and both CSS variants are embedded as string
// constants (JSON encoded) by replacing the markers below.
//
// Usage: node scripts/build-bridge.mjs [--check]
//   --check  exit 1 if the committed bridge is stale instead of rewriting it

import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SRC = path.join(ROOT, "layui_anywidget", "static", "src", "bridge.js");
const RENDERERS = path.join(ROOT, "layui_anywidget", "static", "src", "renderers.js");
const VENDOR = path.join(ROOT, "layui_anywidget", "static", "vendor");
const OUT = path.join(ROOT, "layui_anywidget", "static", "layui-bridge.js");
const WIDGET_CSS = path.join(ROOT, "layui_anywidget", "static", "layui-anywidget.css");

const MARKER = /\/\*__LAYUI_(SOURCE|CSS_FULL|CSS_CORE|CSS_WIDGET|VERSION|RENDERERS)__\*\//g;

const read = async (file) => readFile(path.join(VENDOR, file), "utf8");

const [source, cssFull, cssCore, cssWidget, meta, renderers] = await Promise.all([
  read("layui.js"),
  read("layui.css"),
  read("layui.core.css"),
  readFile(WIDGET_CSS, "utf8"),
  read("layui.version"),
  readFile(RENDERERS, "utf8"),
]);

const embedded = {
  VERSION: JSON.stringify(meta.trim()),
  SOURCE: JSON.stringify(source),
  CSS_FULL: JSON.stringify(cssFull),
  CSS_CORE: JSON.stringify(cssCore),
  CSS_WIDGET: JSON.stringify(cssWidget),
  RENDERERS: renderers,
};

const template = await readFile(SRC, "utf8");
const seen = new Set();
const output = template.replace(MARKER, (match, key) => {
  seen.add(key);
  return embedded[key];
});

for (const key of Object.keys(embedded)) {
  if (!seen.has(key)) {
    throw new Error(`bridge source is missing the ${key} marker`);
  }
}

const check = process.argv.includes("--check");
if (check) {
  const current = await readFile(OUT, "utf8").catch(() => null);
  if (current !== output) {
    console.error(`${path.relative(ROOT, OUT)} is stale; run \`just build\``);
    process.exit(1);
  }
  console.log(`${path.relative(ROOT, OUT)} is up to date`);
} else {
  await writeFile(OUT, output);
  console.log(
    `wrote ${path.relative(ROOT, OUT)} (${(output.length / 1024).toFixed(0)} KB)`,
  );
}
