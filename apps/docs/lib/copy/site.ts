export type SupportedLocale = 'en';

export const defaultLocale: SupportedLocale = 'en';

export const siteCopy = {
  en: {
    appName: 'Mesmer',
    appTagline: 'Vibe-code red-team runs for your AI product.',
    nav: {
      docs: 'Docs',
      blog: 'Blog',
    },
  },
} as const satisfies Record<
  SupportedLocale,
  {
    appName: string;
    appTagline: string;
    nav: {
      docs: string;
      blog: string;
    };
  }
>;

export function getSiteCopy(locale: SupportedLocale = defaultLocale) {
  return siteCopy[locale];
}
