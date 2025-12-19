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
        configureWebpack(config, isServer) {
          // Trellis source directories that need to be compiled
          const trellisSrcDirs = [
            path.resolve(__dirname, '../src/trellis/platforms/browser/client/src'),
            path.resolve(__dirname, '../src/trellis/platforms/common/client/src'),
          ];

          // Find and extend the babel-loader rule to include trellis source
          if (config.module?.rules) {
            for (const rule of config.module.rules) {
              if (typeof rule === 'object' && rule !== null && 'use' in rule) {
                const use = Array.isArray(rule.use) ? rule.use : [rule.use];
                const hasBabel = use.some((u: any) =>
                  typeof u === 'string' ? u.includes('babel-loader') :
                  typeof u?.loader === 'string' ? u.loader.includes('babel-loader') : false
                );
                if (hasBabel && Array.isArray(rule.include)) {
                  rule.include.push(...trellisSrcDirs);
                }
              }
            }
          }

          return {
            resolve: {
              alias: {
                '@trellis/client': path.resolve(__dirname, '../src/trellis/client/src'),
              },
            },
            module: {
              rules: [
                {
                  // Handle .worker-bundle files as raw text (like esbuild's text loader)
                  test: /\.worker-bundle$/,
                  type: 'asset/source',
                },
              ],
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
          href: 'pathname:///trellis/examples/widget-showcase/',
          label: 'Widget Showcase',
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
