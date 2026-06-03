// Remark plugin: rewrite repo-relative links that escape the docs/ root into
// absolute GitHub URLs.
//
// The hand-authored guides and the codegen schema reference cross-link to repo
// source (../apps, ../packages, ../specs, ../examples, ../.ai) that has no route
// in the docs site. Left alone those render as broken in-site links. This walks
// every markdown link/definition, resolves it against the current file, and:
//   - leaves links that stay inside docs/ untouched (Docusaurus resolves them);
//   - rewrites links that land elsewhere in the repo to a github.com URL
//     (/blob/ for files, /tree/ for directories);
//   - leaves external, absolute, and anchor-only links untouched.

import fs from 'node:fs';
import path from 'node:path';

const REPO = 'https://github.com/Space-Wizard-Studios/firebound-proscenio';
const BRANCH = 'main';

// Docusaurus loads this through jiti (CJS context, no import.meta), and runs
// with the cwd at the site dir (apps/docs). Repo root is two levels up.
const REPO_ROOT = path.resolve(process.cwd(), '..', '..');
const DOCS_ROOT = path.join(REPO_ROOT, 'docs');

function isNonRelative(url) {
  // protocol (http:, mailto:), protocol-relative, site-absolute, or anchor-only.
  return /^[a-z][a-z0-9+.-]*:/i.test(url) || url.startsWith('//') || url.startsWith('/') || url.startsWith('#');
}

// `/blob/` for files, `/tree/` for directories. The target is a repo path that
// exists on disk at build time, so stat it instead of guessing from the name
// (an extension heuristic mislabels `LICENSE` / `Makefile` and `some.dir/`).
function githubKind(absTarget) {
  try {
    return fs.statSync(absTarget).isDirectory() ? 'tree' : 'blob';
  } catch {
    return path.extname(absTarget) ? 'blob' : 'tree';
  }
}

function toGithubUrl(absTarget, hash) {
  const repoRel = path.relative(REPO_ROOT, absTarget).split(path.sep).join('/');
  const suffix = hash ? `#${hash}` : '';
  return `${REPO}/${githubKind(absTarget)}/${BRANCH}/${repoRel}${suffix}`;
}

function rewrite(url, fileDir) {
  if (!url || isNonRelative(url)) return url;
  const [rel, hash] = url.split('#');
  if (!rel) return url; // pure anchor already handled, but guard
  const absTarget = path.resolve(fileDir, rel);
  // inside docs/ -> internal, let Docusaurus resolve it.
  if (absTarget === DOCS_ROOT || absTarget.startsWith(DOCS_ROOT + path.sep)) {
    return url;
  }
  // elsewhere in the repo -> point at GitHub.
  if (absTarget.startsWith(REPO_ROOT + path.sep)) {
    return toGithubUrl(absTarget, hash);
  }
  return url;
}

export default function repoLinks() {
  return (tree, file) => {
    const filePath = file.path || (file.history && file.history[file.history.length - 1]);
    if (!filePath) return;
    const fileDir = path.dirname(filePath);

    const walk = (node) => {
      if (!node || typeof node !== 'object') return;
      if ((node.type === 'link' || node.type === 'definition') && typeof node.url === 'string') {
        node.url = rewrite(node.url, fileDir);
      }
      if (Array.isArray(node.children)) {
        for (const child of node.children) walk(child);
      }
    };
    walk(tree);
  };
}
