import Image from 'next/image';
import Link from 'next/link';
import type { ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { getHomeCopy } from '@/lib/copy/home';
import { appName } from '@/lib/shared';
import { createMetadata } from '@/lib/seo/metadata';
import { AttackDefinitionDemo } from './attack-definition-demo';
import { EmbeddingGlobe } from './embedding-globe';

export const metadata = createMetadata({
  path: '/',
});

const copy = getHomeCopy();

function FooterLink({ href, children, className }: { href: string; children: ReactNode; className?: string }) {
  if (href.startsWith('http')) {
    return (
      <a className={className} href={href}>
        {children}
      </a>
    );
  }

  return (
    <Link className={className} href={href}>
      {children}
    </Link>
  );
}

export default function HomePage() {
  const HeroPrimaryIcon = copy.hero.primaryCta.icon;
  const ClosingPrimaryIcon = copy.closing.primaryCta.icon;
  const ClosingSecondaryIcon = copy.closing.secondaryCta.icon;

  return (
    <div id="mesmer-home" className="bg-console-background text-console-foreground">
      <section className="mesmer-hero relative isolate overflow-hidden px-4 sm:px-6 lg:h-[calc(100svh-4rem)] lg:min-h-[620px] lg:px-8">
        <div className="mesmer-hero-grid absolute inset-0 -z-20" aria-hidden="true" />
        <div className="mesmer-hero-light absolute inset-0 -z-10" aria-hidden="true" />

        <div className="mx-auto grid h-full max-w-7xl gap-6 py-9 sm:py-11 lg:grid-cols-[0.78fr_1.22fr] lg:items-center lg:py-0">
          <div className="hero-copy max-w-2xl">
            <div className="hero-kicker mb-6">
              <span>{copy.hero.kicker}</span>
            </div>

            <h1 className="text-6xl font-semibold leading-none tracking-normal text-console-foreground sm:text-7xl lg:text-8xl">
              {appName}
            </h1>
            <p className="mt-5 max-w-xl text-2xl leading-tight text-console-foreground sm:text-3xl">{copy.hero.headlineQuestion}</p>
            <p className="mt-4 max-w-xl text-base leading-7 text-console-muted">{copy.hero.body}</p>

            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Button href={copy.hero.primaryCta.href} className="min-h-11 px-5">
                {copy.hero.primaryCta.label}
                {HeroPrimaryIcon ? <HeroPrimaryIcon aria-hidden="true" className="h-4 w-4" /> : null}
              </Button>
              <Button href={copy.hero.secondaryCta.href} variant="secondary" className="min-h-11 px-5">
                {copy.hero.secondaryCta.label}
              </Button>
            </div>
          </div>

          <div className="hero-globe-wrap">
            <EmbeddingGlobe />
          </div>
        </div>
      </section>

      <section className="message-map-section border-y border-console-border px-4 py-12 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <p className="font-mono text-xs uppercase text-console-accent">{copy.messageMap.eyebrow}</p>
          <div className="mt-3 grid gap-8 lg:grid-cols-[0.46fr_0.54fr] lg:items-center">
            <div>
              <h2 className="max-w-3xl text-3xl font-semibold leading-tight text-console-foreground sm:text-4xl">{copy.messageMap.title}</h2>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-console-muted">{copy.messageMap.body}</p>
              <div className="message-command mt-7">
                <span aria-hidden="true">$</span>
                <code>{copy.messageMap.command}</code>
              </div>
            </div>
            <div className="message-map-stack">
              {copy.messageMap.items.map((item, index) => (
                <article key={item.title} className="message-map-card">
                  <div className="message-map-card-index">{String(index + 1).padStart(2, '0')}</div>
                  <div>
                    <h3>{item.title}</h3>
                    <p>{item.text}</p>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="surprise-section px-4 py-12 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[0.58fr_0.42fr] lg:items-center">
          <div>
            <p className="font-mono text-xs uppercase text-console-amber">{copy.surprise.eyebrow}</p>
            <h2 className="mt-3 max-w-3xl text-3xl font-semibold leading-tight text-console-foreground sm:text-4xl">{copy.surprise.title}</h2>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-console-muted">{copy.surprise.body}</p>
            <p className="surprise-quote mt-5">{copy.surprise.satire}</p>
          </div>
          <div className="surprise-lab">
            <article className="surprise-ticket">
              <div className="surprise-ticket-topline">
                <span>{copy.surprise.ticket.eyebrow}</span>
                <strong>{copy.surprise.ticket.status}</strong>
              </div>
              <h3>{copy.surprise.ticket.title}</h3>
              <div className="surprise-ticket-prompt">
                <span>{copy.surprise.ticket.promptLabel}</span>
                <p>{copy.surprise.ticket.prompt}</p>
              </div>
            </article>

            <div className="surprise-trace" aria-label={copy.surprise.traceLabel}>
              <div className="surprise-trace-header">
                <span>{copy.surprise.traceLabel}</span>
                <span aria-hidden="true">{copy.surprise.traceMarker}</span>
              </div>
              <div className="surprise-trace-rows">
                {copy.surprise.proof.map((item, index) => (
                  <article key={item.label} className="surprise-trace-row">
                    <div className="surprise-trace-label">
                      <span>{String(index + 1).padStart(2, '0')}</span>
                      <p>{item.label}</p>
                    </div>
                    <button
                      type="button"
                      className="surprise-trace-value"
                      aria-describedby={`surprise-trace-example-${index}`}
                    >
                      {item.value}
                    </button>
                    <div id={`surprise-trace-example-${index}`} className="surprise-trace-example" role="tooltip">
                      <span>{item.exampleLabel}</span>
                      <p>{item.example}</p>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="workflow-section border-y border-console-border bg-console-panel/45 px-4 py-12 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[0.56fr_0.44fr] lg:items-center">
          <div>
            <p className="font-mono text-xs uppercase text-console-accent">{copy.workflow.eyebrow}</p>
            <h2 className="mt-3 max-w-3xl text-3xl font-semibold leading-tight text-console-foreground sm:text-4xl">{copy.workflow.title}</h2>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-console-muted">{copy.workflow.body}</p>
            <div className="workflow-rail mt-8">
              {copy.workflow.steps.map((item) => (
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
            <p className="font-mono text-xs uppercase text-console-amber">{copy.safety.eyebrow}</p>
            <h2 className="mt-3 text-2xl font-semibold text-console-foreground">{copy.safety.title}</h2>
            <p className="mt-2 text-sm leading-6 text-console-muted">{copy.safety.body}</p>
          </div>
          <Button href={copy.safety.cta.href} variant="secondary" className="shrink-0">
            {copy.safety.cta.label}
          </Button>
        </div>
      </section>

      <section className="border-t border-console-border bg-console-background px-4 py-12 sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-7xl flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div className="max-w-3xl">
            <p className="font-mono text-xs uppercase text-console-accent">{copy.closing.eyebrow}</p>
            <h2 className="mt-3 text-3xl font-semibold leading-tight text-console-foreground sm:text-4xl">{copy.closing.title}</h2>
            <p className="mt-4 text-sm leading-6 text-console-muted">{copy.closing.body}</p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row md:shrink-0">
            <Button href={copy.closing.primaryCta.href} className="min-h-11 px-5">
              {ClosingPrimaryIcon ? <ClosingPrimaryIcon aria-hidden="true" className="h-4 w-4" /> : null}
              {copy.closing.primaryCta.label}
            </Button>
            <Button href={copy.closing.secondaryCta.href} variant="secondary" className="min-h-11 px-5">
              {ClosingSecondaryIcon ? <ClosingSecondaryIcon aria-hidden="true" className="h-4 w-4" /> : null}
              {copy.closing.secondaryCta.label}
            </Button>
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
                <p className="text-sm text-console-muted">{copy.footer.tagline}</p>
              </div>
            </div>
          </div>
          <nav aria-label={copy.footer.ariaLabel} className="flex flex-wrap gap-3 md:justify-end">
            {copy.footer.links.map((item) => {
              const Icon = item.icon;

              return (
                <FooterLink key={item.label} className="footer-link" href={item.href}>
                  {Icon ? <Icon aria-hidden="true" className="h-4 w-4" /> : null}
                  {item.label}
                </FooterLink>
              );
            })}
          </nav>
        </div>
      </footer>
    </div>
  );
}
