// Generate the Docusaurus i18n/<locale>/ trees from the co-located docs source.
//
// The source of truth is repo-root docs/, where every hand-authored page exists
// side by side per language as <name>-en.md and <name>-pt.md. Docusaurus cannot
// read that layout directly, so this script fans each language out into the
// i18n/<locale>/ shape Docusaurus consumes. English is generated like every
// other language (no implicit default): the config points docs.path at the
// generated i18n/en/ tree. The output is gitignored - this runs on prebuild.
//
// Spec 077. Run: `node scripts/sync-i18n.mjs [--check]`.

import {
  readdirSync,
  statSync,
  readFileSync,
  writeFileSync,
  mkdirSync,
  rmSync,
  cpSync,
  existsSync,
} from 'node:fs';
import {join, dirname, sep} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

// Source language suffix -> Docusaurus (BCP-47) locale. Add a row per language.
const LANGS = [
  {suffix: 'en', locale: 'en'},
  {suffix: 'pt', locale: 'pt-BR'},
];

// Top-level docs/ directories that are single-language generated assets, not
// translated pages: the codegen schema reference and page images. They are
// copied verbatim into every locale tree and skipped by the coverage guard.
const ASSET_DIRS = new Set(['content', 'images']);
// Holds the co-located chrome source (chrome-<lang>.json, code-<lang>.json).
const META_DIR = '_i18n';

const PAGE_EXT = /\.(md|mdx)$/;
const SUFFIXES = LANGS.map((l) => l.suffix);
const LANG_RE = new RegExp(`-(${SUFFIXES.join('|')})\\.(md|mdx)$`);

// The codegen schema pages under content/ import the JSON schema by a path
// relative to the old docs/content/ location; the generated tree sits deeper,
// so re-anchor that import at @site (apps/docs), which is position-independent.
const SCHEMA_IMPORT_RE = /(["'])(?:\.\.\/)+packages\/models\/schemas\//g;
const SCHEMA_IMPORT_ANCHOR = '$1@site/../../packages/models/schemas/';

const asPosix = (p) => p.split(sep).join('/');
const writeJson = (p, obj) => {
  mkdirSync(dirname(p), {recursive: true});
  writeFileSync(p, JSON.stringify(obj, null, 2) + '\n');
};

// Every file under docs/, minus the asset + meta directories, as paths
// relative to docsDir, split into translatable pages (.md/.mdx) and
// language-neutral sidecars (everything else, e.g. _category_.json).
function listSource(docsDir) {
  const all = [];
  const rec = (absDir, relDir) => {
    for (const name of readdirSync(absDir)) {
      if (relDir === '' && (ASSET_DIRS.has(name) || name === META_DIR)) continue;
      const abs = join(absDir, name);
      const rel = relDir ? join(relDir, name) : name;
      if (statSync(abs).isDirectory()) rec(abs, rel);
      else all.push(rel);
    }
  };
  rec(docsDir, '');
  return {
    pages: all.filter((f) => PAGE_EXT.test(f)),
    sidecars: all.filter((f) => !PAGE_EXT.test(f)),
  };
}

// Strip the language suffix from a page path: 01-photoshop-en.md -> 01-photoshop.md.
function stripSuffix(rel, match) {
  return rel.slice(0, rel.length - match[0].length) + '.' + match[2];
}

// Copy the single-language content/ tree into a locale, re-anchoring the codegen
// schema import in each .md/.mdx (see SCHEMA_IMPORT_RE) and copying the rest
// (schema JSON sidecars, _category_.json) verbatim.
function copyContentTree(src, dest) {
  mkdirSync(dest, {recursive: true});
  for (const name of readdirSync(src)) {
    const s = join(src, name);
    const d = join(dest, name);
    if (statSync(s).isDirectory()) copyContentTree(s, d);
    else if (PAGE_EXT.test(name)) {
      writeFileSync(d, readFileSync(s, 'utf8').replace(SCHEMA_IMPORT_RE, SCHEMA_IMPORT_ANCHOR));
    } else {
      writeFileSync(d, readFileSync(s));
    }
  }
}

// Fail fast if any page lacks a language or carries no suffix at all. This is
// the reverse-coverage guard: a new page or a dropped translation breaks the
// build instead of silently shipping an English-only page under pt-BR.
function assertCoverage(pages) {
  const errors = [];
  const groups = new Map(); // stripped page path -> Set of present suffixes

  for (const rel of pages) {
    const m = rel.match(LANG_RE);
    if (!m) {
      errors.push(`untranslated page (no -${SUFFIXES.join('/-')} suffix): docs/${asPosix(rel)}`);
      continue;
    }
    // Key by the page path minus -<lang>.<ext> so a page whose translation
    // is authored with a different extension (guide-en.md + guide-pt.mdx,
    // same route in Docusaurus) groups as one, not two half-missing pages.
    const key = rel.slice(0, rel.length - m[0].length);
    if (!groups.has(key)) groups.set(key, new Set());
    groups.get(key).add(m[1]);
  }

  for (const [key, present] of groups) {
    for (const {suffix} of LANGS) {
      if (!present.has(suffix)) {
        errors.push(
          `missing ${suffix} translation for page: docs/${asPosix(key)} (have: ${[...present].join(', ') || 'none'})`,
        );
      }
    }
  }

  if (errors.length) {
    throw new Error(`sync-i18n coverage check failed:\n  ${errors.join('\n  ')}`);
  }
}

function generate(docsDir, outDir) {
  const {pages, sidecars} = listSource(docsDir);
  assertCoverage(pages);

  for (const {suffix, locale} of LANGS) {
    const localeDir = join(outDir, 'i18n', locale);
    const docsPluginDir = join(localeDir, 'docusaurus-plugin-content-docs');
    const currentDir = join(docsPluginDir, 'current');
    rmSync(localeDir, {recursive: true, force: true});
    mkdirSync(currentDir, {recursive: true});

    // Prose: this language's pages, suffix stripped.
    for (const rel of pages) {
      const m = rel.match(LANG_RE);
      if (m[1] !== suffix) continue;
      const dest = join(currentDir, stripSuffix(rel, m));
      mkdirSync(dirname(dest), {recursive: true});
      writeFileSync(dest, readFileSync(join(docsDir, rel)));
    }

    // Language-neutral sidecars (_category_.json etc.) into every locale tree.
    for (const rel of sidecars) {
      const dest = join(currentDir, rel);
      mkdirSync(dirname(dest), {recursive: true});
      writeFileSync(dest, readFileSync(join(docsDir, rel)));
    }

    // Single-language assets into every locale tree (the two ASSET_DIRS):
    // images copy verbatim; content/ re-anchors its codegen schema import.
    const imagesSrc = join(docsDir, 'images');
    if (existsSync(imagesSrc)) cpSync(imagesSrc, join(currentDir, 'images'), {recursive: true});
    const contentSrc = join(docsDir, 'content');
    if (existsSync(contentSrc)) copyContentTree(contentSrc, join(currentDir, 'content'));

    // Chrome: split chrome-<lang>.json into the Docusaurus per-surface files.
    const chromePath = join(docsDir, META_DIR, `chrome-${suffix}.json`);
    if (existsSync(chromePath)) {
      const chrome = JSON.parse(readFileSync(chromePath, 'utf8'));
      const themeDir = join(localeDir, 'docusaurus-theme-classic');
      writeJson(join(themeDir, 'navbar.json'), chrome.navbar ?? {});
      writeJson(join(themeDir, 'footer.json'), chrome.footer ?? {});
      writeJson(join(docsPluginDir, 'current.json'), chrome.sidebar ?? {});
    }

    // Framework theme-UI strings (code.json): only where a source file exists.
    // pt-BR carries the migrated set; en uses Docusaurus defaults (no file).
    const codePath = join(docsDir, META_DIR, `code-${suffix}.json`);
    if (existsSync(codePath)) {
      mkdirSync(localeDir, {recursive: true});
      writeFileSync(join(localeDir, 'code.json'), readFileSync(codePath));
    }
  }
}

export function sync({docsDir, outDir, check = false} = {}) {
  if (check) {
    assertCoverage(listSource(docsDir).pages);
    return;
  }
  generate(docsDir, outDir);
}

// CLI entry: resolve the real repo paths relative to this script, not cwd.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const scriptDir = dirname(fileURLToPath(import.meta.url));
  const docsDir = join(scriptDir, '..', '..', '..', 'docs');
  const outDir = join(scriptDir, '..'); // apps/docs; the i18n/ tree is written under it
  const check = process.argv.includes('--check');
  try {
    sync({docsDir, outDir, check});
    console.log(
      check
        ? 'sync-i18n: coverage OK'
        : `sync-i18n: generated ${LANGS.map((l) => l.locale).join(', ')} from docs/`,
    );
  } catch (err) {
    console.error(err.message);
    process.exit(1);
  }
}
