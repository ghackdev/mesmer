import type { MetadataRoute } from 'next';
import { getBlogData, getPublishedBlogPosts, source } from '@/lib/source';
import { siteUrl } from '@/lib/shared';

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  const staticRoutes = ['/', '/docs', '/blog'].map((path) => ({
    url: `${siteUrl}${path}`,
    lastModified: now,
  }));
  const docs = source.getPages().map((page) => ({
    url: `${siteUrl}${page.url}`,
    lastModified: now,
  }));
  const blog = getPublishedBlogPosts().map((page) => ({
    url: `${siteUrl}${page.url}`,
    lastModified: new Date(getBlogData(page).updated ?? getBlogData(page).date),
  }));

  return [...staticRoutes, ...docs, ...blog];
}
