import {
  ArrowRight,
  BookOpen,
  Braces,
  FileJson2,
  Gauge,
  GitBranch,
  GitFork,
  LockKeyhole,
  Radar,
  Rss,
  ShieldCheck,
} from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { appName, appTagline, gitConfig } from '@/lib/shared';
import { createMetadata } from '@/lib/seo/metadata';

export const metadata = createMetadata({
  path: '/',
});

const capabilities = [
  {
    icon: GitBranch,
    title: 'Attacks as programs',
    text: 'Compose ordered runtime trees from initialization, generation, constraints, selection, targeting, evaluation, feedback, stopping, transforms, and replay.',
  },
  {
    icon: Radar,
    title: 'Real target boundaries',
    text: 'Exercise LiteLLM models, HTTP JSON, SSE, WebSocket, or Python callables without hiding target interaction behind a one-off script.',
  },
  {
    icon: FileJson2,
    title: 'Replayable evidence',
    text: 'Capture state transitions, compact JSONL traces, token usage, target replay messages, search traces, and reproducible success artifacts.',
  },
  {
    icon: Gauge,
    title: 'Benchmark pressure',
    text: 'Compare single-turn, tree-search, autonomous-agent, and paper-style loops across objectives, targets, budgets, success rates, turns, queries, and cost.',
  },
];

const trace = [
  ['seed', 'objective source loaded: release-readiness canary'],
  ['propose', 'generation.Template produced 1 candidate'],
  ['target', 'targeting.Query wrote replay messages'],
  ['assess', 'evaluation.Contains score=1.0'],
  ['artifact', 'reproduction payload emitted'],
];

const flowNodes = [
  { label: 'Objective', value: 'release token', className: 'left-[7%] top-[16%]' },
  { label: 'Proposer', value: '1 candidate', className: 'left-[36%] top-[7%]' },
  { label: 'Target', value: 'LiteLLM', className: 'right-[8%] top-[36%]' },
  { label: 'Evaluator', value: 'score 1.0', className: 'left-[24%] bottom-[18%]' },
  { label: 'Replay', value: 'artifact', className: 'right-[23%] bottom-[20%]' },
];

export default function HomePage() {
  return (
    <div id="mesmer-home" className="bg-console-background text-console-foreground">
      <section className="relative isolate min-h-[calc(100vh-4rem)] overflow-hidden px-4 py-16 sm:px-6 lg:px-8">
        <div className="console-grid absolute inset-0 -z-10 opacity-70" aria-hidden="true" />
        <div className="mx-auto grid max-w-7xl gap-12 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
          <div className="max-w-3xl">
            <div className="mb-8 flex items-center gap-4">
              <div className="mesmer-sigil" aria-hidden="true">
                <div className="relative z-10 grid h-16 w-16 place-items-center rounded-md border border-console-border bg-console-panel p-1.5">
                  <Image
                    src="/mesmer-logo-transparent.png"
                    width={88}
                    height={88}
                    alt=""
                    priority
                    className="h-full w-full object-contain"
                  />
                </div>
              </div>
              <div>
                <p className="font-mono text-xs uppercase tracking-[0.24em] text-console-muted">
                  authorized safety research harness
                </p>
                <p className="mt-1 text-sm text-console-muted">Python-first · reproducible · composable</p>
              </div>
            </div>

            <h1 className="max-w-4xl text-5xl font-semibold leading-tight text-console-foreground sm:text-6xl lg:text-7xl">
              {appName}
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-console-muted sm:text-xl">{appTagline}</p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Badge>runtime.Program</Badge>
              <Badge>targeting.Query</Badge>
              <Badge>evaluation.Assess</Badge>
              <Badge>replay artifacts</Badge>
            </div>

            <div className="mt-10 flex flex-col gap-3 sm:flex-row">
              <Button href="/docs">
                Read the docs <ArrowRight aria-hidden="true" className="h-4 w-4" />
              </Button>
              <Button href="/blog" variant="secondary">
                Engineering notes
              </Button>
            </div>
          </div>

          <div className="scanline rounded-md border border-console-border bg-console-panel/90 shadow-2xl shadow-black/10">
            <div className="flex items-center justify-between border-b border-console-border px-4 py-3 font-mono text-xs text-console-muted">
              <span>mesmer run --log-format compact</span>
              <span className="live-dot text-console-accent">LIVE</span>
            </div>
            <div className="space-y-4 p-5 font-mono text-sm">
              <div
                className="attack-map relative h-[18rem] overflow-hidden rounded border border-console-border bg-console-background"
                aria-label="Animated Mesmer attack flow visualization"
                role="img"
              >
                <svg className="absolute inset-0 h-full w-full" viewBox="0 0 560 320" aria-hidden="true">
                  <defs>
                    <linearGradient id="attackLine" x1="0" x2="1" y1="0" y2="1">
                      <stop offset="0%" stopColor="var(--console-accent)" />
                      <stop offset="52%" stopColor="var(--console-cyan)" />
                      <stop offset="100%" stopColor="var(--console-amber)" />
                    </linearGradient>
                  </defs>
                  <path className="attack-line delay-0" d="M92 80 C190 32 240 52 284 76" />
                  <path className="attack-line delay-1" d="M284 76 C398 96 462 126 488 160" />
                  <path className="attack-line delay-2" d="M488 160 C400 232 330 250 268 256" />
                  <path className="attack-line delay-3" d="M268 256 C194 224 126 164 92 80" />
                  <path className="attack-line delay-4" d="M284 76 C250 140 246 198 268 256" />
                </svg>
                <div className="absolute left-1/2 top-1/2 grid h-24 w-24 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-md border border-console-accent/55 bg-console-panel/95 shadow-[0_0_36px_rgba(45,213,195,0.22)]">
                  <Image
                    src="/mesmer-logo-transparent.png"
                    width={92}
                    height={92}
                    alt=""
                    className="h-20 w-20 object-contain"
                  />
                </div>
                {flowNodes.map((node, index) => (
                  <div
                    key={node.label}
                    className={`attack-node absolute ${node.className}`}
                    style={{ animationDelay: `${index * 260}ms` }}
                  >
                    <span className="block text-[0.65rem] uppercase text-console-accent">{node.label}</span>
                    <span className="mt-1 block text-xs text-console-muted">{node.value}</span>
                  </div>
                ))}
                <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between rounded border border-console-border bg-console-panel/85 px-3 py-2 text-[0.68rem] text-console-muted">
                  <span>frontier width: 1</span>
                  <span className="text-console-accent">artifact locked</span>
                </div>
              </div>
              <pre
                aria-label="Minimal Mesmer program example"
                tabIndex={0}
                className="overflow-x-auto rounded border border-console-border bg-console-background p-4 text-console-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-console-accent"
              >
                <code>{`from mesmer import runtime, topology, targeting, evaluation

program = runtime.Program(
    topology.Iterate(
        children=[
            targeting.Query(),
            evaluation.Assess(...),
        ],
    ),
)`}</code>
              </pre>
              <ol className="space-y-3" aria-label="Example Mesmer execution trace">
                {trace.map(([event, message], index) => (
                  <li
                    key={event}
                    className="trace-row grid grid-cols-[5.5rem_1fr] gap-3 text-console-muted"
                    style={{ animationDelay: `${index * 180}ms` }}
                  >
                    <span className="text-console-accent">[{event}]</span>
                    <span>{message}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </div>
      </section>

      <section className="border-y border-console-border bg-console-panel/55 px-4 py-14 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-6 md:grid-cols-4">
          {capabilities.map((item) => (
            <article key={item.title} className="rounded-md border border-console-border bg-console-background p-5">
              <item.icon aria-hidden="true" className="mb-5 h-5 w-5 text-console-accent" />
              <h2 className="text-base font-semibold text-console-foreground">{item.title}</h2>
              <p className="mt-3 text-sm leading-6 text-console-muted">{item.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[0.85fr_1.15fr]">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.24em] text-console-amber">safety scope</p>
            <h2 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">
              Built for authorized red-team experiments, not throwaway prompt collections.
            </h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-md border border-console-border bg-console-panel p-5">
              <LockKeyhole aria-hidden="true" className="mb-4 h-5 w-5 text-console-cyan" />
              <h3 className="font-semibold">Permission-first workflows</h3>
              <p className="mt-2 text-sm leading-6 text-console-muted">
                Public examples use benign canary objectives by default, while paper examples keep reproducibility clear and explicit.
              </p>
            </div>
            <div className="rounded-md border border-console-border bg-console-panel p-5">
              <Braces aria-hidden="true" className="mb-4 h-5 w-5 text-console-cyan" />
              <h3 className="font-semibold">Composable primitives</h3>
              <p className="mt-2 text-sm leading-6 text-console-muted">
                The framework favors typed components and services over hidden orchestration, so experiments stay inspectable.
              </p>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-console-border bg-console-panel/70 px-4 py-10 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-8 md:grid-cols-[1.1fr_0.9fr] md:items-end">
          <div>
            <div className="flex items-center gap-3">
              <Image src="/mesmer-logo-transparent.png" width={40} height={40} alt="" className="h-9 w-9 object-contain" />
              <div>
                <p className="font-semibold">{appName}</p>
                <p className="text-sm text-console-muted">Composable safety experiments with replayable evidence.</p>
              </div>
            </div>
            <p className="mt-5 max-w-2xl text-sm leading-6 text-console-muted">
              Built for authorized red-team work, defensive evaluation, benchmark reproduction, and research on systems you own or have permission to test.
            </p>
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
