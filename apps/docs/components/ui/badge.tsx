import type { ReactNode } from 'react';

export function Badge({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-sm border border-console-border bg-console-panel px-2.5 py-1 font-mono text-xs text-console-muted">
      {children}
    </span>
  );
}
