import { blogSource, getBlogData, getBlogImage } from '@/lib/source';
import { appName } from '@/lib/shared';
import { generate as DefaultImage } from 'fumadocs-ui/og';
import { ImageResponse } from 'next/og';
import { notFound } from 'next/navigation';

export const revalidate = false;

export async function GET(_req: Request, { params }: RouteContext<'/og/blog/[...slug]'>) {
  const { slug } = await params;
  const page = blogSource.getPage(slug.slice(0, -1));
  if (!page || getBlogData(page).draft) notFound();

  const data = getBlogData(page);

  return new ImageResponse(
    <DefaultImage title={data.title} description={data.description} site={appName} />,
    {
      width: 1200,
      height: 630,
    },
  );
}

export function generateStaticParams() {
  return blogSource
    .getPages()
    .filter((page) => !getBlogData(page).draft)
    .map((page) => ({
      slug: getBlogImage(page).segments,
    }));
}
