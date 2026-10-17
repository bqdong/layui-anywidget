#!/usr/bin/env node
// Vendor layui 2.13.9 into layui_anywidget/static/vendor.
//
//   node scripts/sync-layui.mjs [--from /path/to/layui/dist] [--version 2.13.9]
//
// Without --from the script downloads the release from jsDelivr.  It then:
//   1. copies layui.js and css/layui.css,
//   2. inlines the icon font (woff2 + ttf) as data URIs so the CSS works from
//      a shadow root / Blob context with no relative URLs,
//   3. derives layui.core.css by removing the global reset rules that would
//      otherwise leak into the host page when injected at document level,
//   4. records the version in vendor/layui.version.
//
// The bridge itself is built by scripts/build-bridge.mjs.

import { mkdir, readFile, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const VENDOR = path.join(ROOT, "layui_anywidget", "static", "vendor");
const DEFAULT_CDN = "https://cdn.jsdelivr.net/npm/layui@%VERSION%/dist";

const args = process.argv.slice(2);
const option = (name, fallback) => {
  const index = args.indexOf(`--${name}`);
  return index >= 0 && args[index + 1] ? args[index + 1] : fallback;
};
const localDir = option("from", null);
const version = option("version", "2.13.9");

const readLocal = async (relative) => {
  const candidates = [
    path.join(localDir, relative),
    path.join(ROOT, localDir, relative),
  ];
  for (const candidate of candidates) {
    if (existsSync(candidate)) return readFile(candidate);
  }
  throw new Error(`cannot find ${relative} under ${localDir}`);
};

const fetchText = async (relative, binary = false) => {
  const url = `${DEFAULT_CDN.replace("%VERSION%", version)}/${relative}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`GET ${url} failed: ${response.status}`);
  }
  return binary ? Buffer.from(await response.arrayBuffer()) : response.text();
};

const readAsset = async (relative, binary = false) => {
  if (localDir) return readLocal(relative);
  return fetchText(relative, binary);
};

// --- font inlining -------------------------------------------------------

const dataUri = (mime, buffer) => `data:${mime};base64,${buffer.toString("base64")}`;

async function inlineFonts(css) {
  const urls = new Set();
  for (const match of css.matchAll(/url\((["']?)([^"')]+)\1\)/g)) {
    const value = match[2].trim();
    if (!value.startsWith("data:") && !value.startsWith("#")) urls.add(value);
  }

  const replacements = new Map();
  for (const url of urls) {
    const file = url.split(/[?#]/)[0];
    const ext = path.extname(file).toLowerCase();
    // Only woff2 and ttf are worth carrying; eot/svg/woff are legacy formats
    // that every supported browser ignores when a woff2 source is present.
    if (ext !== ".woff2" && ext !== ".ttf") continue;
    const mime = ext === ".woff2" ? "font/woff2" : "font/ttf";
    const buffer = await readAsset(path.posix.join("font", path.basename(file)), true);
    replacements.set(url, dataUri(mime, buffer));
  }

  let output = css.replace(/url\((["']?)([^"')]+)\1\)/g, (whole, quote, value) => {
    const trimmed = value.trim();
    if (trimmed.startsWith("data:") || trimmed.startsWith("#")) return whole;
    const file = trimmed.split(/[?#]/)[0];
    const ext = path.extname(file).toLowerCase();
    // Drop legacy font formats: the @font-face list falls through to woff2/ttf.
    if (ext === ".eot" || ext === ".svg" || ext === ".woff") return "url()";
    return replacements.has(trimmed) ? `url(${replacements.get(trimmed)})` : whole;
  });

  // Drop the placeholder `url()` entries left by removed legacy formats, but
  // keep the `src:` keyword: deleting it along with an empty first source
  // (`src:url();`) produces an unparseable @font-face and the icons vanish.
  output = output.replace(/@font-face\{[^}]*\}/g, (block) =>
    block.replace(/src:([^;}]+)([;}])/g, (whole, value, end) => {
      const kept = value.split(",").filter((part) => !/url\(\s*\)/.test(part));
      return kept.length ? `src:${kept.join(",")}${end}` : "";
    }),
  );
  return output;
}

// --- core (reset-free) CSS ----------------------------------------------

const RESET_ELEMENT =
  /^(?:body|html|a|img|li|ol|ul|table|thead|tbody|tfoot|tr|td|th|div|span|h[1-6]|pre|hr|blockquote|dl|dt|dd|p|form|fieldset|legend|input|button|select|textarea|optgroup|option|label|em|i|b|strong|small|code|kbd|sub|sup|address|figure|figcaption|article|aside|footer|header|main|nav|section|details|summary|dialog|template|audio|video|canvas|progress|meter|output)$/i;

function stripReset(css) {
  // Split top-level rules with a brace-depth scan, then drop rules whose
  // every selector starts with a bare element (the reset).  At-rules
  // (font-face, keyframes) are copied verbatim.
  const topLevel = [];
  let start = 0;
  let depth = 0;
  for (let index = 0; index < css.length; index += 1) {
    const char = css[index];
    if (char === "{") depth += 1;
    else if (char === "}") {
      depth -= 1;
      if (depth === 0) {
        topLevel.push(css.slice(start, index + 1));
        start = index + 1;
      }
    }
  }
  if (start < css.length) topLevel.push(css.slice(start));

  // The global reset is the leading contiguous run of bare-element rules.
  // Only that run is dropped; later bare-element rules are component-scoped
  // (e.g. `.laydate-time-list li ol`) and must stay.
  const isBareRule = (rule) => {
    if (rule.trimStart().startsWith("@")) return false;
    const brace = rule.indexOf("{");
    if (brace < 0) return false;
    const selectorText = rule.slice(0, brace).trim();
    if (!selectorText) return false;
    return selectorText.split(",").every((selector) => {
      const base = selector.trim().split(/[\s:.#[]/)[0];
      return RESET_ELEMENT.test(base) || selector.trim() === "html";
    });
  };

  let resetCount = 0;
  while (resetCount < topLevel.length && isBareRule(topLevel[resetCount])) {
    resetCount += 1;
  }
  const kept = topLevel.slice(resetCount);

  // Keep a minimal typography/box-sizing base for portals that lose the
  // notebook's inherited styles.
  const portalBase = [
    ".layui-layer,.layui-laydate,.layui-colorpicker,.layui-popup,.layui-dropdown{",
    "box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;",
    "font-size:14px;line-height:1.6;color:rgba(0,0,0,.85)",
    "}",
    ".layui-layer *,.layui-laydate *,.layui-colorpicker *,.layui-popup *,.layui-dropdown *{box-sizing:border-box}",
  ].join("");

  return kept.join("") + portalBase;
}

// --- main ----------------------------------------------------------------

await mkdir(VENDOR, { recursive: true });

const js = await readAsset("layui.js");
const rawCss = (await readAsset("css/layui.css")).toString("utf8");

const css = await inlineFonts(rawCss);
const core = stripReset(css);

await writeFile(path.join(VENDOR, "layui.js"), js);
await writeFile(path.join(VENDOR, "layui.css"), css);
await writeFile(path.join(VENDOR, "layui.core.css"), core);
await writeFile(path.join(VENDOR, "layui.version"), `${version}\n`);

// Sanity checks: no remaining external font references, reset removed.
if (/url\((?!["']?(?:data:|\)))/.test(css)) {
  throw new Error("layui.css still references external assets");
}
if (/^body\{/m.test(core) || /body\{line-height/.test(core)) {
  throw new Error("layui.core.css still contains the global body reset");
}
// A @font-face without `src:` is ignored by browsers, which silently turns
// every layui icon into a tofu box.
for (const [name, text] of [
  ["layui.css", css],
  ["layui.core.css", core],
]) {
  if (!/@font-face\{font-family:layui-icon;src:url\(data:font\/woff2/.test(text)) {
    throw new Error(`${name} has a malformed layui-icon @font-face`);
  }
}

console.log(`vendored layui ${version}`);
console.log(`  layui.css        ${(css.length / 1024).toFixed(0)} KB`);
console.log(`  layui.core.css   ${(core.length / 1024).toFixed(0)} KB`);
console.log(`  layui.js         ${(js.length / 1024).toFixed(0)} KB`);
