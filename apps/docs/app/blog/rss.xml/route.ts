import { getBlogData, getPublishedBlogPosts } from '@/lib/source';
import { appName, appTagline, siteUrl } from '@/lib/shared';

export const revalidate = false;

function escapeXml(value: string) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;');
}

export async function GET() {
  const items = getPublishedBlogPosts()
    .map((post) => {
      const data = getBlogData(post);
      const url = `${siteUrl}${post.url}`;

      return `<item>
  <title>${escapeXml(data.title)}</title>
  <link>${url}</link>
  <guid>${url}</guid>
  <pubDate>${new Date(data.date).toUTCString()}</pubDate>
  <description>${escapeXml(data.description)}</description>
</item>`;
    })
    .join('\n');

  return new Response(
    `<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>${escapeXml(appName)} Blog</title>
  <link>${siteUrl}/blog</link>
  <description>${escapeXml(appTagline)}</description>
${items}
</channel>
</rss>`,
    {
      headers: {
        'Content-Type': 'application/rss+xml; charset=utf-8',
      },
    },
  );
}
