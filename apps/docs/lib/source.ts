import { blog, docs } from 'collections/server';
import { loader } from 'fumadocs-core/source';
import { lucideIconsPlugin } from 'fumadocs-core/source/lucide-icons';
import { toFumadocsSource } from 'fumadocs-mdx/runtime/server';
import {
  blogContentRoute,
  blogImageRoute,
  blogRoute,
  docsContentRoute,
  docsImageRoute,
  docsRoute,
} from './shared';
import { i18n } from './i18n';

// See https://fumadocs.dev/docs/headless/source-api for more info
export const source = loader({
  baseUrl: docsRoute,
  i18n,
  source: docs.toFumadocsSource(),
  plugins: [lucideIconsPlugin()],
});

export const blogSource = loader({
  baseUrl: blogRoute,
  i18n,
  source: toFumadocsSource(blog, []),
});

export type BlogPage = (typeof blogSource)['$inferPage'];
export type BlogData = (typeof blog)[number];

export function getBlogData(page: BlogPage): BlogData {
  return page.data as BlogData;
}

export function getPageImage(page: (typeof source)['$inferPage']) {
  const segments = [...page.slugs, 'image.png'];

  return {
    segments,
    url: `${docsImageRoute}/${segments.join('/')}`,
  };
}

export function getPageMarkdownUrl(page: (typeof source)['$inferPage']) {
  const segments = [...page.slugs, 'content.md'];

  return {
    segments,
    url: `${docsContentRoute}/${segments.join('/')}`,
  };
}

export async function getLLMText(page: (typeof source)['$inferPage']) {
  const processed = await page.data.getText('processed');

  return `# ${page.data.title} (${page.url})

${processed}`;
}

export function getBlogImage(page: BlogPage) {
  const segments = [...page.slugs, 'image.png'];

  return {
    segments,
    url: `${blogImageRoute}/${segments.join('/')}`,
  };
}

export function getBlogMarkdownUrl(page: BlogPage) {
  const segments = [...page.slugs, 'content.md'];

  return {
    segments,
    url: `${blogContentRoute}/${segments.join('/')}`,
  };
}

export async function getBlogLLMText(page: BlogPage) {
  const data = getBlogData(page);
  const processed = await page.data.getText('processed');

  return `# ${data.title} (${page.url})

${processed}`;
}

export function getPublishedBlogPosts() {
  return blogSource
    .getPages()
    .filter((page) => !getBlogData(page).draft)
    .sort((a, b) => Date.parse(getBlogData(b).date) - Date.parse(getBlogData(a).date));
}
