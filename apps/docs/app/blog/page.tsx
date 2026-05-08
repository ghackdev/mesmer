import { ArrowUpRight, CalendarDays, ChevronRight, X } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import { getBlogData, getPublishedBlogPosts } from '@/lib/source';
import { createMetadata } from '@/lib/seo/metadata';
import { appName, blogRoute, docsRoute, gitConfig } from '@/lib/shared';

export const metadata = createMetadata({
  title: 'Blog',
  description: 'Engineering notes about Mesmer, composable LLM red-team workflows, and reproducible safety benchmarking.',
  path: '/blog',
});

function tagUrl(tag: string) {
  return `${blogRoute}?tag=${encodeURIComponent(tag)}`;
}

export default async function BlogIndex(props: PageProps<'/blog'>) {
  const searchParams = await props.searchParams;
  const rawTag = searchParams.tag;
  const activeTag = typeof rawTag === 'string' ? rawTag : Array.isArray(rawTag) ? rawTag[0] : undefined;
  const posts = getPublishedBlogPosts();
  const tags = [...new Set(posts.flatMap((post) => getBlogData(post).tags))].sort();
  const visiblePosts = activeTag ? posts.filter((post) => getBlogData(post).tags.includes(activeTag)) : posts;
  const githubUrl = `https://github.com/${gitConfig.user}/${gitConfig.repo}`;

  return (
    <main className="bg-console-background px-4 py-14 text-console-foreground sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <nav className="mb-12 flex flex-wrap items-center justify-between gap-4" aria-label="Blog navigation">
          <Link href="/" className="inline-flex items-center gap-3 text-console-foreground hover:text-console-accent">
            <Image src="/mesmer-logo-transparent.png" width={44} height={44} alt="" className="h-11 w-11 object-contain" priority />
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
          <span className="text-console-foreground">Blog</span>
          {activeTag ? (
            <>
              <ChevronRight aria-hidden="true" className="h-3.5 w-3.5" />
              <span className="text-console-foreground">{activeTag}</span>
            </>
          ) : null}
        </nav>

        <p className="font-mono text-xs uppercase tracking-[0.24em] text-console-muted">Mesmer blog</p>
        <h1 className="mt-4 max-w-3xl text-4xl font-semibold tracking-tight sm:text-5xl">
          Notes from the operator runtime.
        </h1>
        <p className="mt-5 max-w-2xl text-base leading-7 text-console-muted">
          Research updates, architecture notes, implementation guides, and reproducibility writeups for authorized LLM safety testing.
        </p>

        {tags.length > 0 ? (
          <div className="mt-8 flex flex-wrap gap-2" aria-label="Blog tags">
            {tags.map((tag) => (
              <Link
                key={tag}
                href={tagUrl(tag)}
                className={[
                  'rounded-sm border px-2 py-1 font-mono text-xs transition-colors',
                  activeTag === tag
                    ? 'border-console-accent bg-console-accent/10 text-console-accent'
                    : 'border-console-border bg-console-panel text-console-muted hover:border-console-accent hover:text-console-accent',
                ].join(' ')}
              >
                {tag}
              </Link>
            ))}
            {activeTag ? (
              <Link href={blogRoute} className="inline-flex items-center gap-1 rounded-sm border border-console-border bg-console-background px-2 py-1 font-mono text-xs text-console-muted hover:border-console-accent hover:text-console-accent">
                <X aria-hidden="true" className="h-3.5 w-3.5" />
                clear
              </Link>
            ) : null}
          </div>
        ) : null}

        <div className="mt-12 grid gap-5">
          {visiblePosts.map((post) => (
            <article key={post.url} className="rounded-md border border-console-border bg-console-panel p-6">
              <div className="flex flex-wrap items-center gap-3 font-mono text-xs text-console-muted">
                <span className="inline-flex items-center gap-2">
                  <CalendarDays aria-hidden="true" className="h-3.5 w-3.5" />
                  {new Intl.DateTimeFormat('en', { dateStyle: 'medium' }).format(new Date(getBlogData(post).date))}
                </span>
                {getBlogData(post).tags.map((tag: string) => (
                  <Link key={tag} href={tagUrl(tag)} className="hover:text-console-accent">
                    {tag}
                  </Link>
                ))}
              </div>
              <h2 className="mt-4 text-2xl font-semibold">
                <Link href={post.url} className="inline-flex items-center gap-2 hover:text-console-accent">
                  {getBlogData(post).title}
                  <ArrowUpRight aria-hidden="true" className="h-4 w-4" />
                </Link>
              </h2>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-console-muted">{getBlogData(post).description}</p>
            </article>
          ))}
          {visiblePosts.length === 0 ? (
            <div className="rounded-md border border-console-border bg-console-panel p-6 text-sm text-console-muted">
              No posts found for <span className="font-mono text-console-foreground">{activeTag}</span>.
            </div>
          ) : null}
        </div>
      </div>
    </main>
  );
}
