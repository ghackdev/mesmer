import { ArrowLeft, ArrowRight, ArrowUpRight, ChevronRight } from 'lucide-react';
import { blogSource, getBlogData, getBlogImage, getBlogMarkdownUrl, getPublishedBlogPosts } from '@/lib/source';
import { getMDXComponents } from '@/components/mdx';
import { createMetadata } from '@/lib/seo/metadata';
import { appName, blogRoute, docsRoute, gitConfig, siteUrl } from '@/lib/shared';
import { DocsBody, MarkdownCopyButton, ViewOptionsPopover } from 'fumadocs-ui/layouts/docs/page';
import Image from 'next/image';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import type { Metadata } from 'next';

function tagUrl(tag: string) {
  return `${blogRoute}?tag=${encodeURIComponent(tag)}`;
}

export default async function BlogPost(props: PageProps<'/blog/[slug]'>) {
  const params = await props.params;
  const page = blogSource.getPage([params.slug]);
  if (!page || getBlogData(page).draft) notFound();

  const data = getBlogData(page);
  const MDX = data.body;
  const markdownUrl = getBlogMarkdownUrl(page).url;
  const posts = getPublishedBlogPosts();
  const postIndex = posts.findIndex((post) => post.url === page.url);
  const newerPost = postIndex > 0 ? posts[postIndex - 1] : null;
  const olderPost = postIndex >= 0 && postIndex < posts.length - 1 ? posts[postIndex + 1] : null;
  const githubUrl = `https://github.com/${gitConfig.user}/${gitConfig.repo}`;
  const published = new Date(data.date).toISOString();
  const updated = new Date(data.updated ?? data.date).toISOString();
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: data.title,
    description: data.description,
    datePublished: published,
    dateModified: updated,
    author: data.authors.map((name: string) => ({ '@type': 'Person', name })),
    publisher: { '@type': 'Organization', name: appName },
    mainEntityOfPage: `${siteUrl}${page.url}`,
  };

  return (
    <main className="bg-console-background px-4 py-10 text-console-foreground sm:px-6 lg:px-8">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <div className="mx-auto max-w-5xl">
        <nav className="mb-8 flex flex-wrap items-center justify-between gap-4" aria-label="Blog navigation">
          <Link href="/" className="inline-flex items-center gap-3 text-console-foreground hover:text-console-accent">
            <Image src="/mesmer-logo-transparent.png" width={44} height={44} alt={appName} className="h-11 w-11 object-contain" priority />
            <span className="font-mono text-xs uppercase tracking-[0.24em]">Mesmer</span>
          </Link>
          <div className="flex flex-wrap items-center gap-2 font-mono text-xs text-console-muted">
            <Link href={docsRoute} className="rounded-sm border border-console-border bg-console-panel px-3 py-2 hover:border-console-accent hover:text-console-accent">
              Docs
            </Link>
            <Link href={blogRoute} className="rounded-sm border border-console-accent bg-console-accent/10 px-3 py-2 text-console-accent">
              Blog
            </Link>
            <a href={githubUrl} className="inline-flex items-center gap-2 rounded-sm border border-console-border bg-console-panel px-3 py-2 hover:border-console-accent hover:text-console-accent">
              <ArrowUpRight aria-hidden="true" className="h-3.5 w-3.5" />
              GitHub
            </a>
          </div>
        </nav>
        <nav className="mb-8 flex flex-wrap items-center gap-2 font-mono text-xs text-console-muted" aria-label="Breadcrumb">
          <Link href="/" className="hover:text-console-accent">
            Home
          </Link>
          <ChevronRight aria-hidden="true" className="h-3.5 w-3.5" />
          <Link href={blogRoute} className="hover:text-console-accent">
            Blog
          </Link>
          <ChevronRight aria-hidden="true" className="h-3.5 w-3.5" />
          <span className="max-w-full truncate text-console-foreground sm:max-w-xl">{data.title}</span>
        </nav>
      </div>

      <article className="mx-auto max-w-5xl">
        <header className="relative overflow-hidden rounded-lg border border-console-border bg-console-panel/70 p-6 shadow-2xl shadow-console-foreground/5 sm:p-8 lg:p-10">
          <div className="console-grid absolute inset-0 opacity-35" aria-hidden="true" />
          <div className="relative">
            <div className="flex items-center gap-4">
              <div className="grid h-14 w-14 place-items-center rounded-md border border-console-border bg-console-background p-1.5 shadow-[0_0_28px_rgba(6,115,107,0.14)]">
                <Image src="/mesmer-logo-transparent.png" width={72} height={72} alt="" priority className="h-full w-full object-contain" />
              </div>
              <div>
                <p className="font-mono text-xs uppercase tracking-[0.24em] text-console-muted">Mesmer blog</p>
                <p className="mt-1 text-sm text-console-muted">Research notes from the safety harness</p>
              </div>
            </div>
            <h1 className="mt-8 max-w-4xl text-4xl font-semibold leading-tight tracking-tight text-console-foreground sm:text-5xl lg:text-6xl">
              {data.title}
            </h1>
            <p className="mt-5 max-w-3xl text-base leading-7 text-console-muted sm:text-lg">{data.description}</p>
            <div className="mt-7 flex flex-wrap items-center gap-3 border-t border-console-border pt-5 font-mono text-xs text-console-muted">
              <span>{new Intl.DateTimeFormat('en', { dateStyle: 'long' }).format(new Date(data.date))}</span>
              {data.authors.map((author: string) => (
                <span key={author}>{author}</span>
              ))}
              {data.tags.map((tag: string) => (
                <Link key={tag} href={tagUrl(tag)} className="rounded-sm border border-console-border bg-console-background px-2 py-1 hover:border-console-accent hover:text-console-accent">
                  {tag}
                </Link>
              ))}
              <MarkdownCopyButton markdownUrl={markdownUrl} />
              <ViewOptionsPopover markdownUrl={markdownUrl} />
            </div>
          </div>
        </header>
        <div className="mx-auto mt-10 max-w-4xl">
          <DocsBody className="mesmer-blog-body">
            <MDX components={getMDXComponents()} />
          </DocsBody>
        </div>
        <footer className="mx-auto mt-12 max-w-4xl border-t border-console-border pt-8">
          <div className="grid gap-4 sm:grid-cols-2">
            {newerPost ? (
              <Link href={newerPost.url} className="rounded-md border border-console-border bg-console-panel p-5 transition-colors hover:border-console-accent">
                <span className="inline-flex items-center gap-2 font-mono text-xs text-console-muted">
                  <ArrowLeft aria-hidden="true" className="h-4 w-4" />
                  Newer post
                </span>
                <span className="mt-4 block text-lg font-semibold leading-snug text-console-foreground">{getBlogData(newerPost).title}</span>
              </Link>
            ) : (
              <Link href={blogRoute} className="rounded-md border border-console-border bg-console-panel p-5 transition-colors hover:border-console-accent">
                <span className="inline-flex items-center gap-2 font-mono text-xs text-console-muted">
                  <ArrowLeft aria-hidden="true" className="h-4 w-4" />
                  Back to blog
                </span>
                <span className="mt-4 block text-lg font-semibold leading-snug text-console-foreground">All Mesmer blog posts</span>
              </Link>
            )}
            {olderPost ? (
              <Link href={olderPost.url} className="rounded-md border border-console-border bg-console-panel p-5 text-right transition-colors hover:border-console-accent">
                <span className="inline-flex items-center justify-end gap-2 font-mono text-xs text-console-muted">
                  Older post
                  <ArrowRight aria-hidden="true" className="h-4 w-4" />
                </span>
                <span className="mt-4 block text-lg font-semibold leading-snug text-console-foreground">{getBlogData(olderPost).title}</span>
              </Link>
            ) : (
              <Link href={blogRoute} className="rounded-md border border-console-border bg-console-panel p-5 text-right transition-colors hover:border-console-accent">
                <span className="inline-flex items-center justify-end gap-2 font-mono text-xs text-console-muted">
                  Blog index
                  <ArrowRight aria-hidden="true" className="h-4 w-4" />
                </span>
                <span className="mt-4 block text-lg font-semibold leading-snug text-console-foreground">All Mesmer blog posts</span>
              </Link>
            )}
          </div>
        </footer>
      </article>
    </main>
  );
}

export function generateStaticParams() {
  return getPublishedBlogPosts().map((page) => ({
    slug: page.slugs[0],
  }));
}

export async function generateMetadata(props: PageProps<'/blog/[slug]'>): Promise<Metadata> {
  const params = await props.params;
  const page = blogSource.getPage([params.slug]);
  if (!page || getBlogData(page).draft) notFound();

  const data = getBlogData(page);

  return createMetadata({
    title: data.title,
    description: data.description,
    path: page.url,
    image: data.image ?? getBlogImage(page).url,
    type: 'article',
  });
}
