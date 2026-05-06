import { blogSource, getBlogData, getBlogLLMText, getBlogMarkdownUrl } from '@/lib/source';
import { notFound } from 'next/navigation';

export const revalidate = false;

export async function GET(_req: Request, { params }: RouteContext<'/llms.mdx/blog/[[...slug]]'>) {
  const { slug } = await params;
  const page = blogSource.getPage(slug?.slice(0, -1));
  if (!page || getBlogData(page).draft) notFound();

  return new Response(await getBlogLLMText(page), {
    headers: {
      'Content-Type': 'text/markdown; charset=utf-8',
    },
  });
}

export function generateStaticParams() {
  return blogSource
    .getPages()
    .filter((page) => !getBlogData(page).draft)
    .map((page) => ({
      slug: getBlogMarkdownUrl(page).segments,
    }));
}
