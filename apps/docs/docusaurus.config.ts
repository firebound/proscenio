import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

import remarkGithubAdmonitionsToDirectives from 'remark-github-admonitions-to-directives';

import repoLinks from './src/remark/repo-links.mjs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

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
        docsDir: '../../docs',
      },
    ],
  ],

  // GitHub Pages project site: https://space-wizard-studios.github.io/firebound-proscenio/
  url: 'https://space-wizard-studios.github.io',
  baseUrl: '/firebound-proscenio/',

  organizationName: 'Space-Wizard-Studios',
  projectName: 'firebound-proscenio',

  // Docs cross-link to repo source (../apps, ../packages, ../specs) that does
  // not exist as a site route. The repo-links remark plugin rewrites those to
  // github.com URLs before resolution; kept as 'warn' as a safety net.
  onBrokenLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          // The hand-authored guides (docs/*.md) plus the codegen schema
          // reference (docs/content/**) are served from the repo docs/ folder.
          path: '../../docs',
          routeBasePath: '/',
          sidebarPath: './sidebars.ts',
          // Run before Docusaurus's own remark pipeline:
          // - repoLinks rewrites repo-source links to github.com URLs before the
          //   broken-link resolver checks them.
          // - github-admonitions converts GitHub `> [!NOTE]` alert blockquotes
          //   into Docusaurus `:::note` directives so the same syntax renders
          //   styled on both GitHub and the docs site.
          beforeDefaultRemarkPlugins: [repoLinks, remarkGithubAdmonitionsToDirectives],
          editUrl:
            'https://github.com/Space-Wizard-Studios/firebound-proscenio/tree/main/docs/',
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
          sidebarId: 'apiSidebar',
          position: 'left',
          label: 'Schema reference',
        },
        {
          type: 'docSidebar',
          sidebarId: 'blenderSidebar',
          position: 'left',
          label: 'Blender addon',
        },
        {
          href: 'https://github.com/Space-Wizard-Studios/firebound-proscenio',
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
            {label: 'Features', to: '/project/features'},
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/Space-Wizard-Studios/firebound-proscenio',
            },
            {
              label: 'Firebound',
              href: 'https://github.com/Space-Wizard-Studios/firebound',
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
