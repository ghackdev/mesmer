import { siteCopy } from './copy/site';

export const appName = 'Mesmer';
export const appTagline = siteCopy.en.appTagline;
export const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? 'https://mesmer.dev';
export const docsRoute = '/docs';
export const blogRoute = '/blog';
export const docsImageRoute = '/og/docs';
export const blogImageRoute = '/og/blog';
export const docsContentRoute = '/llms.mdx/docs';
export const blogContentRoute = '/llms.mdx/blog';

// fill this with your actual GitHub info, for example:
export const gitConfig = {
  user: 'ghackdev',
  repo: 'mesmer',
  branch: 'main',
};
