import {
  ArrowRight,
  BookOpen,
  GitFork,
  Radar,
  Route,
  Rss,
  Scale,
  ShieldCheck,
  Target,
  type LucideIcon,
} from 'lucide-react';
import type { SupportedLocale } from './site';

type LinkCopy = {
  label: string;
  href: string;
  icon?: LucideIcon;
};

type HomeCopy = {
  hero: {
    kicker: string;
    headlineQuestion: string;
    body: string;
    primaryCta: LinkCopy;
    secondaryCta: LinkCopy;
  };
  messageMap: {
    eyebrow: string;
    title: string;
    body: string;
    command: string;
    items: {
      title: string;
      text: string;
    }[];
  };
  surprise: {
    eyebrow: string;
    title: string;
    body: string;
    satire: string;
    ticket: {
      eyebrow: string;
      title: string;
      status: string;
      promptLabel: string;
      prompt: string;
    };
    traceLabel: string;
    traceMarker: string;
    proof: {
      label: string;
      value: string;
      exampleLabel: string;
      example: string;
    }[];
  };
  workflow: {
    eyebrow: string;
    title: string;
    body: string;
    steps: {
      icon: LucideIcon;
      label: string;
      text: string;
    }[];
  };
  safety: {
    eyebrow: string;
    title: string;
    body: string;
    cta: LinkCopy;
  };
  closing: {
    eyebrow: string;
    title: string;
    body: string;
    primaryCta: LinkCopy;
    secondaryCta: LinkCopy;
  };
  footer: {
    ariaLabel: string;
    tagline: string;
    links: LinkCopy[];
  };
};

export const homeCopy = {
  en: {
    hero: {
      kicker: 'authorized AI red-team lab',
      headlineQuestion: 'Your AI app has a text box. That means it has an attack surface.',
      body: 'Mesmer turns weird user input into Python red-team recipes you can run, inspect, replay, and benchmark against systems you own or have permission to test.',
      primaryCta: {
        label: 'Run your first red-team',
        href: '/docs/first-run',
        icon: ArrowRight,
      },
      secondaryCta: {
        label: 'See the evidence',
        href: '/docs/observability-and-replay',
      },
    },
    messageMap: {
      eyebrow: 'message map',
      title: 'Red-teaming should not require becoming a security team first.',
      body: 'AI apps can be built in plain English now. The testing loop should be just as approachable, but still reproducible enough for serious engineering.',
      command: 'mesmer map --audience builders --output evidence',
      items: [
        {
          title: 'Accessible',
          text: 'Start from one authorized objective and one target. No exploit folklore required before the first useful run.',
        },
        {
          title: 'Reproducible',
          text: 'Keep the exact messages, evaluations, state transitions, and replay artifacts instead of a screenshot and a nervous memory.',
        },
        {
          title: 'Composable',
          text: 'Grow from one probe into frontier search, prompt-pattern experiments, fuzzing, and benchmarks without rebuilding the harness.',
        },
      ],
    },
    surprise: {
      eyebrow: 'the uncomfortable part',
      title: 'A jailbreak can look like normal product feedback.',
      body: 'Prompt injection does not always arrive as code. Sometimes it is just a patient user, a text box, and a few attempts at wording the request differently. That is why Mesmer treats red-team work as a repeatable experiment, not a magic prompt hunt.',
      satire:
        'Your AI product does not need a hoodie-wearing villain. Sometimes it only needs a user with too much curiosity and a text box.',
      ticket: {
        eyebrow: 'feedback #1842',
        title: 'The assistant is too strict. Can it be more helpful?',
        status: 'looks harmless',
        promptLabel: 'hidden test shape',
        prompt: 'same request, different wording, repeated until a boundary moves',
      },
      traceLabel: 'authorized trace',
      traceMarker: '///',
      proof: [
        {
          label: 'Start',
          value: 'one canary objective',
          exampleLabel: 'example objective',
          example: 'Get ReleaseDesk to emit RELEASE_READY only when the authorized readiness check is satisfied.',
        },
        {
          label: 'Search',
          value: 'branch, score, keep winners',
          exampleLabel: 'example technique',
          example: 'FrontierSearch(iterations=2, branching=3, width=2) explores support-ticket wording and keeps the strongest candidate.',
        },
        {
          label: 'Evidence',
          value: 'replayable target messages',
          exampleLabel: 'example artifact',
          example:
            'Replay includes the exact user message, target response, evaluator score, and operator trace that produced the result.',
        },
      ],
    },
    workflow: {
      eyebrow: 'teach me something new',
      title: 'A red-team run is a recipe you can inspect.',
      body: 'Pick the technique that matches the question, plug in the target and evaluator, then let Mesmer preserve the evidence.',
      steps: [
        {
          icon: Target,
          label: 'Ask one risky question',
          text: 'Use SingleTurnProbe for one objective, one target call, and one evaluator.',
        },
        {
          icon: Route,
          label: 'Search better wording',
          text: 'Use FrontierSearch when you want branching, selection, scoring, and a replayable winner.',
        },
        {
          icon: GitFork,
          label: 'Fuzz variations',
          text: 'Use PopulationFuzzing for seed pools, mutators, reward updates, and repeated trials.',
        },
        {
          icon: Radar,
          label: 'Reuse known tactics',
          text: 'Pull from prompt-pattern libraries while keeping the attack recipe readable.',
        },
        {
          icon: Scale,
          label: 'Compare runs',
          text: 'Wrap several attacks in a Benchmark and report shared metrics across objectives.',
        },
      ],
    },
    safety: {
      eyebrow: 'safety scope',
      title: 'Designed for authorized evaluation.',
      body: 'Mesmer is for defensive testing, benchmark reproduction, and research on systems you own or have permission to test.',
      cta: {
        label: 'Safety scope',
        href: '/docs/safety-scope',
      },
    },
    closing: {
      eyebrow: 'takeaway',
      title: 'The goal is not to prove your AI is impossible to jailbreak.',
      body: 'The goal is to stop guessing. Run the test, keep the trace, compare the technique, and know exactly what happened.',
      primaryCta: {
        label: 'Read the docs',
        href: '/docs',
        icon: BookOpen,
      },
      secondaryCta: {
        label: 'Open GitHub',
        href: 'https://github.com/ghackdev/mesmer',
        icon: GitFork,
      },
    },
    footer: {
      ariaLabel: 'Footer',
      tagline: 'Programmable red-team experiments with replayable evidence.',
      links: [
        {
          label: 'Docs',
          href: '/docs',
          icon: BookOpen,
        },
        {
          label: 'Blog',
          href: '/blog',
          icon: Rss,
        },
        {
          label: 'GitHub',
          href: 'https://github.com/ghackdev/mesmer',
          icon: GitFork,
        },
        {
          label: 'Safety',
          href: '/docs/safety-scope',
          icon: ShieldCheck,
        },
      ],
    },
  },
} as const satisfies Record<SupportedLocale, HomeCopy>;

export function getHomeCopy(locale: SupportedLocale = 'en') {
  return homeCopy[locale];
}
