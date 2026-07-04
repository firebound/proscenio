import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

import remarkGithubAdmonitionsToDirectives from 'remark-github-admonitions-to-directives';

import repoLinks from './src/remark/repo-links.mjs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

// The docs source is co-located under repo-root docs/ as <name>-en.md /
// <name>-pt.md; scripts/sync-i18n.mjs fans each language out into the Docusaurus
// i18n/<locale>/ trees on prebuild. English is a generated pack like every other
// language: the docs plugin and the search index both read the generated en tree,
// not docs/ directly. Spec 077.
const GENERATED_EN_DOCS = './i18n/en/docusaurus-plugin-content-docs/current';

const config: Config = {
  title: 'Proscenio',
  tagline: 'A Photoshop -> Blender -> Godot pipeline for 2D cutout animation',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  markdown: {
    // .md -> CommonMark, .mdx -> MDX. Keeps the codegen schema reference (full
    // of `{` and `<`) from being parsed as MDX and blowing up the build.
    format: 'detect',
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },

  themes: [
    '@docusaurus/theme-mermaid',
    'docusaurus-json-schema-plugin',
    [
      '@easyops-cn/docusaurus-search-local',
      {
        hashed: true,
        indexBlog: false,
        docsRouteBasePath: '/',
        docsDir: GENERATED_EN_DOCS,
        // Index pt-BR pages with the Portuguese lunr stemmer alongside en
        // (spec 072 D7); without 'pt' the pt-BR locale search degrades.
        language: ['en', 'pt'],
      },
    ],
  ],

  // GitHub Pages project site: https://firebound.github.io/proscenio/
  url: 'https://firebound.github.io',
  baseUrl: '/proscenio/',

  organizationName: 'firebound',
  projectName: 'proscenio',

  // Docs cross-link to repo source (../apps, ../packages, ../specs) that does
  // not exist as a site route. The repo-links remark plugin rewrites those to
  // github.com URLs before resolution; kept as 'warn' as a safety net.
  onBrokenLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'pt-BR'],
    localeConfigs: {
      'pt-BR': {
        label: 'Português (Brasil)',
        htmlLang: 'pt-BR',
        direction: 'ltr',
      },
    },
  },

  plugins: [
    [
      '@docusaurus/plugin-client-redirects',
      {
        // PR2 folded the standalone 09-validation.md page into
        // pipeline.md#validate; this keeps the old slug from 404ing.
        redirects: [
          {from: '/blender-addon/validation', to: '/tools/blender-addon/pipeline#validate'},
        ],
      },
    ],
  ],

  presets: [
    [
      'classic',
      {
        docs: {
          // Served from the generated English pack (see GENERATED_EN_DOCS
          // above). The tree mirrors the old docs/ layout exactly (numbered
          // prefixes and doc ids unchanged); only its source moved to the
          // co-located docs/**-en.md via the sync.
          path: GENERATED_EN_DOCS,
          routeBasePath: '/',
          sidebarPath: './sidebars.ts',
          // Run before Docusaurus's own remark pipeline:
          // - repoLinks rewrites repo-source links to github.com URLs before the
          //   broken-link resolver checks them.
          // - github-admonitions converts GitHub `> [!NOTE]` alert blockquotes
          //   into Docusaurus `:::note` directives so the same syntax renders
          //   styled on both GitHub and the docs site.
          beforeDefaultRemarkPlugins: [repoLinks, remarkGithubAdmonitionsToDirectives],
          // Docs are served from the generated tree; point Edit at the
          // co-located source (docs/<path>-<lang>.md) instead of the artifact.
          // The codegen schema reference under content/ is single-language.
          editUrl: ({locale, docPath}) => {
            const lang = locale === 'pt-BR' ? 'pt' : 'en';
            const source = docPath.startsWith('content/')
              ? docPath
              : docPath.replace(/\.mdx?$/, (ext) => `-${lang}${ext}`);
            return `https://github.com/firebound/proscenio/tree/main/docs/${source}`;
          },
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/docusaurus-social-card.jpg',
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Proscenio',
      logo: {
        alt: 'Proscenio logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'guidesSidebar',
          position: 'left',
          label: 'Guides',
        },
        {
          type: 'docSidebar',
          sidebarId: 'projectSidebar',
          position: 'left',
          label: 'Project',
        },
        {
          type: 'docSidebar',
          sidebarId: 'toolsSidebar',
          position: 'left',
          label: 'Tools',
        },
        {
          type: 'localeDropdown',
          position: 'right',
        },
        {
          href: 'https://github.com/firebound/proscenio',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {label: 'Walkthrough', to: '/guides/basic'},
            {label: 'Architecture', to: '/project/architecture'},
            {label: 'Tools', to: '/tools/blender-addon'},
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/firebound/proscenio',
            },
            {
              label: 'Firebound',
              href: 'https://github.com/firebound/firebound',
            },
          ],
        },
      ],
      copyright: `Copyright (c) ${new Date().getFullYear()} Space Wizard Studios. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['powershell', 'python', 'gdscript', 'json', 'bash', 'toml'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
