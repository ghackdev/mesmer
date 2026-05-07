import { ArrowRight, BookOpen, GitFork, Radar, Route, Rss, Scale, ShieldCheck, Target } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { appName, appTagline, gitConfig } from '@/lib/shared';
import { createMetadata } from '@/lib/seo/metadata';
import { AttackDefinitionDemo } from './attack-definition-demo';
import { EmbeddingGlobe } from './embedding-globe';

export const metadata = createMetadata({
  path: '/',
});

const workflow = [
  {
    icon: Target,
    label: 'Objective',
    text: 'Define the authorized behavior once, then reuse it across flows and targets.',
  },
  {
    icon: Route,
    label: 'Technique',
    text: 'Choose or write the attack recipe: single-turn probe, frontier search, population fuzzing, or your own algorithm.',
  },
  {
    icon: GitFork,
    label: 'Operators',
    text: 'Extend behavior with typed state transitions for proposal, selection, target calls, evaluation, feedback, and rewards.',
  },
  {
    icon: Radar,
    label: 'Target',
    text: 'Swap LiteLLM, HTTP, SSE, WebSocket, or callable boundaries without rewriting the technique.',
  },
  {
    icon: Scale,
    label: 'Replay',
    text: 'Keep exact messages, judgement, and operator transitions that produced the result.',
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
              Compose attack techniques, run them against authorized targets, and keep replayable evidence of what happened.
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
              Compose jailbreak experiments as techniques and operators.
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

          <AttackDefinitionDemo />
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
