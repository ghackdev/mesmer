import type { BaseLayoutProps } from 'fumadocs-ui/layouts/shared';
import { defineI18nUI } from 'fumadocs-ui/i18n';
import Image from 'next/image';
import { appName, blogRoute, docsRoute, gitConfig } from './shared';
import { i18n } from './i18n';
import { getSiteCopy } from './copy/site';

export const i18nUI = defineI18nUI(i18n, {
  en: {
    displayName: 'English',
  },
});

export function baseOptions(locale = 'en'): BaseLayoutProps {
  const copy = getSiteCopy();

  return {
    nav: {
      title: (
        <span className="mesmer-nav-brand">
          <Image src="/mesmer-logo-transparent.png" width={40} height={40} alt={appName} className="mesmer-nav-logo" priority />
        </span>
      ),
    },
    links: [
      {
        text: copy.nav.docs,
        url: docsRoute,
        active: 'nested-url',
      },
      {
        text: copy.nav.blog,
        url: blogRoute,
        active: 'nested-url',
      },
    ],
    githubUrl: `https://github.com/${gitConfig.user}/${gitConfig.repo}`,
    i18n: true,
    ...(locale ? {} : {}),
  };
}
