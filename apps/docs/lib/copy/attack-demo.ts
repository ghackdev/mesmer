import { BarChart3, FlaskConical, GitBranch, KeyRound, Repeat2, type LucideIcon } from 'lucide-react';
import type { SupportedLocale } from './site';

export type DemoMode = 'single' | 'frontier' | 'population' | 'patterns' | 'benchmark';

export type CodeToken = {
  text: string;
  tone?: 'keyword' | 'symbol' | 'string' | 'number' | 'comment' | 'call' | 'field';
};

export type CodeLine = {
  number: number;
  tokens: CodeToken[];
  active?: boolean;
};

type UseCaseCopy = {
  id: DemoMode;
  label: string;
  detail: string;
  heading: string;
  subheading: string;
  icon: LucideIcon;
  chips: string[];
};

type AttackDemoCopy = {
  ariaLabel: string;
  eyebrow: string;
  controlsAriaLabel: string;
  codeAriaLabel: (label: string) => string;
  defaultMode: DemoMode;
  useCases: UseCaseCopy[];
  codeByMode: Record<DemoMode, CodeLine[]>;
};

const t = (text: string, tone?: CodeToken['tone']): CodeToken => ({ text, tone });

export const attackDemoCopy = {
  en: {
    ariaLabel: 'Interactive Mesmer use-case examples',
    eyebrow: 'Declarative attack recipes',
    controlsAriaLabel: 'Mesmer use cases',
    codeAriaLabel: (label: string) => `${label} Mesmer code example`,
    defaultMode: 'frontier',
    useCases: [
      {
        id: 'single',
        label: 'Ask one risky question',
        detail: 'One prompt, one target call.',
        heading: 'Single-turn canary probe',
        subheading: 'Ask one authorized question and score the response.',
        icon: KeyRound,
        chips: ['1 target call', 'exact token check', 'minimal recipe'],
      },
      {
        id: 'frontier',
        label: 'Search better wording',
        detail: 'Branch, score, keep winners.',
        heading: 'Support-router escalation eval',
        subheading: 'Explore ticket wording while preserving the winning branch.',
        icon: GitBranch,
        chips: ['3 x 2 budget', 'selector included', 'replayable path'],
      },
      {
        id: 'population',
        label: 'Fuzz variations',
        detail: 'Mutate seeds and reward hits.',
        heading: 'JBFuzz-style mutation run',
        subheading: 'Load prompt seeds, mutate them, and update rewards.',
        icon: FlaskConical,
        chips: ['seed pool', 'UCB selector', 'reward ledger'],
      },
      {
        id: 'patterns',
        label: 'Reuse known tactics',
        detail: 'Reuse prompt tactics safely.',
        heading: 'Encoded readiness check',
        subheading: 'Materialize a prompt pattern without changing the target.',
        icon: Repeat2,
        chips: ['pattern library', 'base64 transform', 'same run shape'],
      },
      {
        id: 'benchmark',
        label: 'Compare runs',
        detail: 'Compare techniques fairly.',
        heading: 'Router benchmark suite',
        subheading: 'Run several techniques against shared objectives and metrics.',
        icon: BarChart3,
        chips: ['shared objectives', 'multiple attacks', 'same metrics'],
      },
    ],
    codeByMode: {
      single: [
        { number: 1, active: true, tokens: [t('attack', 'field'), t(' = '), t('techniques', 'call'), t('.SingleTurnProbe(')] },
        { number: 2, active: true, tokens: [t('  name', 'field'), t('='), t('"release_token_probe"', 'string'), t(',')] },
        { number: 3, active: true, tokens: [t('  evaluate', 'field'), t('='), t('ops', 'call'), t('.Evaluate('), t('evaluators', 'call'), t('.Contains(text='), t('"RELEASE_READY"', 'string'), t(')),')] },
        { number: 4, active: true, tokens: [t('  stop', 'field'), t('='), t('ops', 'call'), t('.StopWhen('), t('conditions', 'call'), t('.ScoreAtLeast('), t('1', 'number'), t(')),')] },
        { number: 5, tokens: [t(')')] },
        { number: 6, tokens: [t('')] },
        { number: 7, active: true, tokens: [t('run', 'field'), t(' = '), t('Run', 'call'), t('(')] },
        { number: 8, active: true, tokens: [t('  objectives', 'field'), t('='), t('ObjectiveSource', 'call'), t('.single('), t('"return the release token"', 'string'), t('),')] },
        { number: 9, active: true, tokens: [t('  attack', 'field'), t('='), t('attack', 'field'), t(', target='), t('target', 'field'), t(',')] },
        { number: 10, tokens: [t(')')] },
      ],
      frontier: [
        { number: 1, active: true, tokens: [t('attack', 'field'), t(' = '), t('techniques', 'call'), t('.FrontierSearch(')] },
        { number: 2, active: true, tokens: [t('  name', 'field'), t('='), t('"support_router_escalation"', 'string'), t(',')] },
        { number: 3, active: true, tokens: [t('  iterations', 'field'), t('='), t('2', 'number'), t(', branching='), t('3', 'number'), t(', width='), t('2', 'number'), t(',')] },
        { number: 4, active: true, tokens: [t('  expand', 'field'), t('='), t('ops', 'call'), t('.Propose('), t('proposers', 'call'), t('.Template()),')] },
        { number: 5, active: true, tokens: [t('  select', 'field'), t('='), t('ops', 'call'), t('.Select('), t('selectors', 'call'), t('.KeywordOverlapSelector()),')] },
        { number: 6, active: true, tokens: [t('  evaluate', 'field'), t('='), t('ops', 'call'), t('.Evaluate('), t('evaluators', 'call'), t('.Contains(text='), t('"ESCALATE_TIER_2"', 'string'), t(')),')] },
        { number: 7, active: true, tokens: [t('  stop', 'field'), t('='), t('ops', 'call'), t('.StopWhen('), t('conditions', 'call'), t('.ScoreAtLeast('), t('1', 'number'), t(')),')] },
        { number: 8, tokens: [t(')')] },
        { number: 9, tokens: [t('')] },
        { number: 10, active: true, tokens: [t('result', 'field'), t(' = '), t('await', 'keyword'), t(' '), t('Runner', 'call'), t('(log_format='), t('"compact"', 'string'), t(').run(run)')] },
      ],
      population: [
        { number: 1, active: true, tokens: [t('attack', 'field'), t(' = '), t('techniques', 'call'), t('.PopulationFuzzing(')] },
        { number: 2, active: true, tokens: [t('  name', 'field'), t('='), t('"jbfuzz"', 'string'), t(', iterations='), t('20', 'number'), t(', branching='), t('4', 'number'), t(',')] },
        { number: 3, active: true, tokens: [t('  seeds', 'field'), t('='), t('sources', 'call'), t('.CsvSeedPoolSource(path='), t('"seeds.csv"', 'string'), t('),')] },
        { number: 4, active: true, tokens: [t('  generate', 'field'), t('='), t('ops', 'call'), t('.GenerateFromPopulation(')] },
        { number: 5, active: true, tokens: [t('    selector', 'field'), t('='), t('selectors', 'call'), t('.UCBSeedSelector(),')] },
        { number: 6, active: true, tokens: [t('    mutator', 'field'), t('='), t('mutators', 'call'), t('.LexicalSubstitutionMutator(),')] },
        { number: 7, active: true, tokens: [t('  ),')] },
        { number: 8, active: true, tokens: [t('  evaluate', 'field'), t('='), t('ops', 'call'), t('.Evaluate('), t('evaluators', 'call'), t('.Contains(text='), t('"ALLOW"', 'string'), t(')),')] },
        { number: 9, active: true, tokens: [t('  reward', 'field'), t('='), t('ops', 'call'), t('.AssignReward(), stop='), t('ops', 'call'), t('.StopWhen(...),')] },
        { number: 10, tokens: [t(')')] },
      ],
      patterns: [
        { number: 1, active: true, tokens: [t('pattern', 'field'), t(' = '), t('prompts', 'call'), t('.PromptLibrary(')] },
        { number: 2, active: true, tokens: [t('  patterns', 'field'), t('='), t('prompts', 'call'), t('.BUILTIN_PROMPT_PATTERNS')] },
        { number: 3, active: true, tokens: [t(').tagged({'), t('"readiness"', 'string'), t('}).patterns['), t('0', 'number'), t(']')] },
        { number: 4, tokens: [t('')] },
        { number: 5, active: true, tokens: [t('objective', 'field'), t(' = '), t('Objective', 'call'), t('(')] },
        { number: 6, active: true, tokens: [t('  goal', 'field'), t('='), t('"return RELEASE_READY"', 'string'), t(',')] },
        { number: 7, active: true, tokens: [t('  initial_state', 'field'), t('='), t('InitialState', 'call'), t('.from_prompt('), t('encoded_prompt', 'field'), t('),')] },
        { number: 8, active: true, tokens: [t('  metadata', 'field'), t('={'), t('"prompt_pattern_id"', 'string'), t(': pattern.id},')] },
        { number: 9, tokens: [t(')')] },
        { number: 10, active: true, tokens: [t('run', 'field'), t(' = '), t('Run', 'call'), t('(objectives='), t('ObjectiveSource', 'call'), t('.single(objective), attack=attack, target=target)')] },
      ],
      benchmark: [
        { number: 1, active: true, tokens: [t('benchmark', 'field'), t(' = '), t('Benchmark', 'call'), t('(')] },
        { number: 2, active: true, tokens: [t('  name', 'field'), t('='), t('"ops_router_eval"', 'string'), t(',')] },
        { number: 3, active: true, tokens: [t('  objectives', 'field'), t('='), t('ObjectiveSource', 'call'), t('.list(objectives),')] },
        { number: 4, active: true, tokens: [t('  attacks', 'field'), t('=[')] },
        { number: 5, active: true, tokens: [t('    single_turn('), t('"single_turn"', 'string'), t('),')] },
        { number: 6, active: true, tokens: [t('    frontier_search('), t('"frontier_search"', 'string'), t('),')] },
        { number: 7, active: true, tokens: [t('    population_fuzzing('), t('"jbfuzz"', 'string'), t('),')] },
        { number: 8, active: true, tokens: [t('  ], targets=['), t('target', 'field'), t('],')] },
        { number: 9, active: true, tokens: [t('  metrics', 'field'), t('=['), t('AttackSuccessRate', 'call'), t('(), '), t('MeanQueries', 'call'), t('()],')] },
        { number: 10, tokens: [t(')')] },
      ],
    },
  },
} as const satisfies Record<SupportedLocale, AttackDemoCopy>;

export function getAttackDemoCopy(locale: SupportedLocale = 'en') {
  return attackDemoCopy[locale];
}
