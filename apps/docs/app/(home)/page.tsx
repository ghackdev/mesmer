import { ArrowRight, BookOpen, Box, FileJson2, GitFork, Radar, Route, Rss, Scale, ShieldCheck, Target } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { appName, appTagline, gitConfig } from '@/lib/shared';
import { createMetadata } from '@/lib/seo/metadata';
import { EmbeddingGlobe } from './embedding-globe';

export const metadata = createMetadata({
  path: '/',
});

const workflow = [
  {
    icon: Target,
    label: 'Objective',
    text: 'State the behavior you are authorized to test.',
  },
  {
    icon: Route,
    label: 'Program',
    text: 'Encode the technique as an ordered runtime tree.',
  },
  {
    icon: Radar,
    label: 'Target',
    text: 'Query real model, HTTP, SSE, WebSocket, or callable boundaries.',
  },
  {
    icon: Scale,
    label: 'Judge',
    text: 'Record whether the target crossed the intended boundary.',
  },
  {
    icon: FileJson2,
    label: 'Replay',
    text: 'Keep target-visible messages and compact evidence.',
  },
];

export default function HomePage() {
  return (
    <div id="mesmer-home" className="bg-console-background text-console-foreground">
      <section className="mesmer-hero relative isolate overflow-hidden px-4 sm:px-6 lg:h-[calc(100svh-4rem)] lg:min-h-[620px] lg:px-8">
        <div className="mesmer-hero-grid absolute inset-0 -z-20" aria-hidden="true" />
        <div className="mesmer-hero-light absolute inset-0 -z-10" aria-hidden="true" />

        <div className="mx-auto grid h-full max-w-7xl gap-6 py-9 sm:py-11 lg:grid-cols-[0.78fr_1.22fr] lg:items-center lg:py-0">
          <div className="hero-copy max-w-2xl">
            <div className="hero-kicker mb-6">
              <span>authorized jailbreak research lab</span>
            </div>

            <h1 className="text-6xl font-semibold leading-none tracking-normal text-console-foreground sm:text-7xl lg:text-8xl">
              {appName}
            </h1>
            <p className="mt-5 max-w-xl text-2xl leading-tight text-console-foreground sm:text-3xl">{appTagline}</p>
            <p className="mt-4 max-w-xl text-base leading-7 text-console-muted">
              Compose attack programs, run them against authorized targets, and keep replayable evidence of what happened.
            </p>

            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Button href="/docs" className="min-h-11 px-5">
                Read the docs <ArrowRight aria-hidden="true" className="h-4 w-4" />
              </Button>
              <Button href="/blog" variant="secondary" className="min-h-11 px-5">
                Engineering notes
              </Button>
            </div>
          </div>

          <div className="hero-globe-wrap">
            <EmbeddingGlobe />
          </div>
        </div>
      </section>

      <section className="workflow-section border-y border-console-border bg-console-panel/45 px-4 py-12 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[0.56fr_0.44fr] lg:items-center">
          <div>
            <p className="font-mono text-xs uppercase text-console-accent">how mesmer thinks</p>
            <h2 className="mt-3 max-w-3xl text-3xl font-semibold leading-tight text-console-foreground sm:text-4xl">
              From a jailbreak idea to evidence you can inspect.
            </h2>
            <div className="workflow-rail mt-8">
              {workflow.map((item) => (
                <article key={item.label} className="workflow-step">
                  <div className="workflow-step-icon">
                    <item.icon aria-hidden="true" className="h-4 w-4" />
                  </div>
                  <div>
                    <h3>{item.label}</h3>
                    <p>{item.text}</p>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className="artifact-panel">
            <div className="mb-5 flex items-center justify-between gap-4">
              <span className="font-mono text-xs uppercase text-console-muted">output artifact</span>
              <Box aria-hidden="true" className="h-5 w-5 text-console-accent" />
            </div>
            <dl>
              <div>
                <dt>target replay</dt>
                <dd>messages preserved</dd>
              </div>
              <div>
                <dt>judgement</dt>
                <dd>score + reason</dd>
              </div>
              <div>
                <dt>search trace</dt>
                <dd>path to reproduction</dd>
              </div>
            </dl>
          </div>
        </div>
      </section>

      <section className="px-4 py-12 sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-7xl flex-col gap-6 rounded-md border border-console-border bg-console-panel/65 p-6 sm:p-7 md:flex-row md:items-center md:justify-between">
          <div className="max-w-3xl">
            <p className="font-mono text-xs uppercase text-console-amber">safety scope</p>
            <h2 className="mt-3 text-2xl font-semibold text-console-foreground">Designed for authorized evaluation.</h2>
            <p className="mt-2 text-sm leading-6 text-console-muted">
              Mesmer is for defensive testing, benchmark reproduction, and research on systems you own or have permission to test.
            </p>
          </div>
          <Button href="/docs/safety-scope" variant="secondary" className="shrink-0">
            Safety scope
          </Button>
        </div>
      </section>

      <footer className="border-t border-console-border bg-console-panel/70 px-4 py-10 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-8 md:grid-cols-[1.1fr_0.9fr] md:items-end">
          <div>
            <div className="flex items-center gap-3">
              <Image src="/mesmer-logo-transparent.png" width={40} height={40} alt="" className="h-9 w-9 object-contain" />
              <div>
                <p className="font-semibold">{appName}</p>
                <p className="text-sm text-console-muted">Reproducible LLM safety experiments with replayable evidence.</p>
              </div>
            </div>
          </div>
          <nav aria-label="Footer" className="flex flex-wrap gap-3 md:justify-end">
            <Link className="footer-link" href="/docs">
              <BookOpen aria-hidden="true" className="h-4 w-4" />
              Docs
            </Link>
            <Link className="footer-link" href="/blog">
              <Rss aria-hidden="true" className="h-4 w-4" />
              Blog
            </Link>
            <a className="footer-link" href={`https://github.com/${gitConfig.user}/${gitConfig.repo}`}>
              <GitFork aria-hidden="true" className="h-4 w-4" />
              GitHub
            </a>
            <Link className="footer-link" href="/docs/safety-scope">
              <ShieldCheck aria-hidden="true" className="h-4 w-4" />
              Safety
            </Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
