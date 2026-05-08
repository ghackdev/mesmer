import type { SupportedLocale } from './site';

type EmbeddingGlobeCopy = {
  ariaLabel: string;
  safeNodeLabels: Record<number, string>;
  vulnerableTraceLabels: {
    personaShift: string[];
    roleConfusion: string[];
    formatTrap: string[];
  };
};

export const embeddingGlobeCopy = {
  en: {
    ariaLabel: 'Rotating embedding network with safe and vulnerable paths',
    safeNodeLabels: {
      5: 'refusal',
      13: 'boundary held',
      16: 'clarify',
      28: 'policy',
      37: 'ask permission',
      43: 'safe answer',
      52: 'sanitize',
      57: 'redirect',
      68: 'benign',
    },
    vulnerableTraceLabels: {
      personaShift: ['persona shift', 'authority mimic', 'constraint gap', 'jailbreak path'],
      roleConfusion: ['role confusion', 'policy gap', 'hidden request', 'leak branch'],
      formatTrap: ['format trap', 'evaluator miss', 'unsafe continuation'],
    },
  },
} as const satisfies Record<SupportedLocale, EmbeddingGlobeCopy>;

export function getEmbeddingGlobeCopy(locale: SupportedLocale = 'en'): EmbeddingGlobeCopy {
  return embeddingGlobeCopy[locale];
}
