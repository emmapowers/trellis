import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import path from 'path';

const config: Config = {
  title: 'Trellis',
  tagline: 'Reactive UI framework for Python',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://emmapowers.github.io',
  baseUrl: '/trellis/',

  organizationName: 'emmapowers',
  projectName: 'trellis',

  onBrokenLinks: 'warn',  // TODO: Change to 'throw' when links are fixed
  onBrokenMarkdownLinks: 'warn',

  markdown: {
    format: 'detect', // Use mdx for .mdx, md for .md
    mermaid: true,
  },

  themes: ['@docusaurus/theme-mermaid'],

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/emmapowers/trellis/tree/main/docs/',
          routeBasePath: '/', // Docs at root instead of /docs/
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  plugins: [
    function trellisClientPlugin() {
      return {
        name: 'trellis-client-webpack',
        configureWebpack() {
          return {
            resolve: {
              alias: {
                '@trellis/client': path.resolve(__dirname, '../src/trellis/client/src'),
              },
            },
          };
        },
      };
    },
  ],

  themeConfig: {
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Trellis',
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        {
          href: 'pathname:///trellis/playground/',
          label: 'Playground',
          position: 'left',
        },
        {
          href: 'https://github.com/emmapowers/trellis',
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
            {
              label: 'Getting Started',
              to: '/',
            },
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/emmapowers/trellis',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Trellis. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'bash'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
