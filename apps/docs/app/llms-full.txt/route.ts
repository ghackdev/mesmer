import { getBlogLLMText, getLLMText, getPublishedBlogPosts, source } from '@/lib/source';

export const revalidate = false;

export async function GET() {
  const scan = [...source.getPages().map(getLLMText), ...getPublishedBlogPosts().map(getBlogLLMText)];
  const scanned = await Promise.all(scan);

  return new Response(scanned.join('\n\n'));
}
