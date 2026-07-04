import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join, dirname} from 'node:path';

import {sync} from './sync-i18n.mjs';

// Build a throwaway co-located docs tree; return {docsDir, outDir, cleanup}.
function scaffold(files) {
  const root = mkdtempSync(join(tmpdir(), 'i18n-sync-'));
  const docsDir = join(root, 'docs');
  const outDir = join(root, 'out');
  for (const [rel, body] of Object.entries(files)) {
    const abs = join(docsDir, rel);
    mkdirSync(dirname(abs), {recursive: true});
    writeFileSync(abs, body);
  }
  return {docsDir, outDir, cleanup: () => rmSync(root, {recursive: true, force: true})};
}

const EN = join('i18n', 'en', 'docusaurus-plugin-content-docs', 'current');
const PT = join('i18n', 'pt-BR', 'docusaurus-plugin-content-docs', 'current');

test('generates both locale trees, suffix stripped, NN- prefix + content intact', (t) => {
  const {docsDir, outDir, cleanup} = scaffold({
    'index-en.md': '# Home EN',
    'index-pt.md': '# Home PT',
    '00-guides/01-basic/01-photoshop-en.md': '# Photoshop EN',
    '00-guides/01-basic/01-photoshop-pt.md': '# Photoshop PT',
    '_i18n/chrome-en.json': JSON.stringify({navbar: {}, footer: {}, sidebar: {}}),
    '_i18n/chrome-pt.json': JSON.stringify({navbar: {}, footer: {}, sidebar: {}}),
  });
  t.after(cleanup);

  sync({docsDir, outDir});

  assert.equal(readFileSync(join(outDir, EN, 'index.md'), 'utf8'), '# Home EN');
  assert.equal(readFileSync(join(outDir, PT, 'index.md'), 'utf8'), '# Home PT');
  // NN- prefix survives on dirs and stem; only the -en/-pt language suffix is stripped.
  assert.equal(
    readFileSync(join(outDir, EN, '00-guides', '01-basic', '01-photoshop.md'), 'utf8'),
    '# Photoshop EN',
  );
  assert.equal(
    readFileSync(join(outDir, PT, '00-guides', '01-basic', '01-photoshop.md'), 'utf8'),
    '# Photoshop PT',
  );
});

test('copies single-language assets (content/, images/) into BOTH locale trees', (t) => {
  const {docsDir, outDir, cleanup} = scaffold({
    'index-en.md': 'en',
    'index-pt.md': 'pt',
    'content/proscenio.mdx': 'SCHEMA',
    'content/README.md': 'CONTENT-README',
    'images/logo.txt': 'IMG',
    '_i18n/chrome-en.json': JSON.stringify({navbar: {}, footer: {}, sidebar: {}}),
    '_i18n/chrome-pt.json': JSON.stringify({navbar: {}, footer: {}, sidebar: {}}),
  });
  t.after(cleanup);

  sync({docsDir, outDir});

  for (const cur of [EN, PT]) {
    assert.equal(readFileSync(join(outDir, cur, 'content', 'proscenio.mdx'), 'utf8'), 'SCHEMA');
    assert.equal(readFileSync(join(outDir, cur, 'content', 'README.md'), 'utf8'), 'CONTENT-README');
    assert.equal(readFileSync(join(outDir, cur, 'images', 'logo.txt'), 'utf8'), 'IMG');
  }
  // content/README.md is a single-language asset, never treated as a page needing a -pt sibling.
});

test('copies language-neutral sidecars (_category_.json) into both locale trees', (t) => {
  const {docsDir, outDir, cleanup} = scaffold({
    '00-guides/01-basic/01-photoshop-en.md': 'en',
    '00-guides/01-basic/01-photoshop-pt.md': 'pt',
    '00-guides/01-basic/_category_.json': '{"label":"Basic walkthrough"}',
    'index-en.md': 'en',
    'index-pt.md': 'pt',
    '_i18n/chrome-en.json': JSON.stringify({navbar: {}, footer: {}, sidebar: {}}),
    '_i18n/chrome-pt.json': JSON.stringify({navbar: {}, footer: {}, sidebar: {}}),
  });
  t.after(cleanup);

  sync({docsDir, outDir});

  for (const cur of [EN, PT]) {
    assert.equal(
      readFileSync(join(outDir, cur, '00-guides', '01-basic', '_category_.json'), 'utf8'),
      '{"label":"Basic walkthrough"}',
    );
  }
  // A _category_.json is Docusaurus sidebar config, not a translatable page, so
  // the coverage guard must not demand an -en/-pt pair for it.
});

test('rewrites the codegen schema import to a location-independent @site anchor', (t) => {
  const {docsDir, outDir, cleanup} = scaffold({
    'index-en.md': 'en',
    'index-pt.md': 'pt',
    'content/proscenio/document.mdx':
      'import schema from "../../../packages/models/schemas/proscenio.schema.json";\n' +
      'import {withDefs} from "@site/src/schema/with-defs";\n',
    '_i18n/chrome-en.json': JSON.stringify({navbar: {}, footer: {}, sidebar: {}}),
    '_i18n/chrome-pt.json': JSON.stringify({navbar: {}, footer: {}, sidebar: {}}),
  });
  t.after(cleanup);

  sync({docsDir, outDir});

  // The relative import was anchored to docs/content/'s depth; the generated
  // tree is deeper, so the sync re-anchors it at @site (apps/docs) which is
  // position-independent. The @site helper import is left untouched.
  for (const cur of [EN, PT]) {
    const out = readFileSync(join(outDir, cur, 'content', 'proscenio', 'document.mdx'), 'utf8');
    assert.match(out, /import schema from "@site\/\.\.\/\.\.\/packages\/models\/schemas\/proscenio\.schema\.json";/);
    assert.doesNotMatch(out, /"\.\.\/\.\.\/\.\.\/packages/);
    assert.match(out, /import \{withDefs\} from "@site\/src\/schema\/with-defs";/);
  }
});

test('splits chrome into navbar/footer/current.json; code.json for pt only', (t) => {
  const {docsDir, outDir, cleanup} = scaffold({
    'index-en.md': 'en',
    'index-pt.md': 'pt',
    '_i18n/chrome-en.json': JSON.stringify({
      navbar: {'item.label.Guides': {message: 'Guides'}},
      footer: {'link.title.Docs': {message: 'Docs'}},
      sidebar: {'sidebar.guidesSidebar.category.Guides': {message: 'Guides'}},
    }),
    '_i18n/chrome-pt.json': JSON.stringify({
      navbar: {'item.label.Guides': {message: 'Guias'}},
      footer: {'link.title.Docs': {message: 'Documentos'}},
      sidebar: {'sidebar.guidesSidebar.category.Guides': {message: 'Guias'}},
    }),
    '_i18n/code-pt.json': JSON.stringify({'theme.NotFound.title': {message: 'Pagina nao encontrada'}}),
  });
  t.after(cleanup);

  sync({docsDir, outDir});

  const rd = (p) => JSON.parse(readFileSync(join(outDir, p), 'utf8'));
  assert.deepEqual(
    rd(join('i18n', 'en', 'docusaurus-theme-classic', 'navbar.json')),
    {'item.label.Guides': {message: 'Guides'}},
  );
  assert.deepEqual(
    rd(join('i18n', 'en', 'docusaurus-theme-classic', 'footer.json')),
    {'link.title.Docs': {message: 'Docs'}},
  );
  assert.deepEqual(
    rd(join('i18n', 'en', 'docusaurus-plugin-content-docs', 'current.json')),
    {'sidebar.guidesSidebar.category.Guides': {message: 'Guides'}},
  );
  assert.deepEqual(
    rd(join('i18n', 'pt-BR', 'docusaurus-theme-classic', 'navbar.json')),
    {'item.label.Guides': {message: 'Guias'}},
  );
  // code.json: pt carries the migrated framework strings; en uses Docusaurus defaults (no file).
  assert.deepEqual(rd(join('i18n', 'pt-BR', 'code.json')), {'theme.NotFound.title': {message: 'Pagina nao encontrada'}});
  assert.ok(!existsSync(join(outDir, 'i18n', 'en', 'code.json')));
});

test('coverage guard: a page missing its -pt sibling fails, naming the page', (t) => {
  const {docsDir, outDir, cleanup} = scaffold({
    'index-en.md': 'en',
    'index-pt.md': 'pt',
    '00-guides/03-iterate-en.md': 'only english',
    '_i18n/chrome-en.json': JSON.stringify({navbar: {}, footer: {}, sidebar: {}}),
    '_i18n/chrome-pt.json': JSON.stringify({navbar: {}, footer: {}, sidebar: {}}),
  });
  t.after(cleanup);

  assert.throws(() => sync({docsDir, outDir}), /03-iterate/);
});

test('coverage guard: a suffix-less .md in a translated directory fails', (t) => {
  const {docsDir, outDir, cleanup} = scaffold({
    'index-en.md': 'en',
    'index-pt.md': 'pt',
    '00-guides/orphan.md': 'no language suffix',
    '_i18n/chrome-en.json': JSON.stringify({navbar: {}, footer: {}, sidebar: {}}),
    '_i18n/chrome-pt.json': JSON.stringify({navbar: {}, footer: {}, sidebar: {}}),
  });
  t.after(cleanup);

  assert.throws(() => sync({docsDir, outDir}), /orphan/);
});

test('--check mode runs the guard without writing output', (t) => {
  const {docsDir, outDir, cleanup} = scaffold({
    'index-en.md': 'en',
    'index-pt.md': 'pt',
    '_i18n/chrome-en.json': JSON.stringify({navbar: {}, footer: {}, sidebar: {}}),
    '_i18n/chrome-pt.json': JSON.stringify({navbar: {}, footer: {}, sidebar: {}}),
  });
  t.after(cleanup);

  sync({docsDir, outDir, check: true});
  assert.ok(!existsSync(outDir), 'check mode must not create the output tree');
});
