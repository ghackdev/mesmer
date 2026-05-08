'use client';

import { useState } from 'react';
import { getAttackDemoCopy, type DemoMode } from '@/lib/copy/attack-demo';

const copy = getAttackDemoCopy();

export function AttackDefinitionDemo() {
  const [mode, setMode] = useState<DemoMode>(copy.defaultMode);
  const active = copy.useCases.find((item) => item.id === mode) ?? copy.useCases[1];
  const ActiveIcon = active.icon;

  return (
    <div className="attack-demo" aria-label={copy.ariaLabel}>
      <div className="attack-demo-header">
        <div>
          <p>{copy.eyebrow}</p>
          <h3>{active.heading}</h3>
          <span>{active.subheading}</span>
        </div>
        <ActiveIcon aria-hidden="true" className="h-5 w-5" />
      </div>

      <div className="attack-demo-controls" aria-label={copy.controlsAriaLabel}>
        {copy.useCases.map((item) => {
          const Icon = item.icon;
          const selected = item.id === mode;

          return (
            <button
              key={item.id}
              type="button"
              className="attack-demo-control"
              data-active={selected}
              onClick={() => setMode(item.id)}
              onFocus={() => setMode(item.id)}
              onPointerEnter={() => setMode(item.id)}
            >
              <Icon aria-hidden="true" className="h-4 w-4" />
              <span>
                <strong>{item.label}</strong>
                <small>{item.detail}</small>
              </span>
            </button>
          );
        })}
      </div>

      <pre className="attack-code" aria-label={copy.codeAriaLabel(active.label)} tabIndex={0}>
        <code>
          {copy.codeByMode[mode].map((line) => (
            <span key={line.number} className="attack-code-line" data-active={'active' in line ? line.active : undefined}>
              <span className="attack-code-number">{line.number}</span>
              <span className="attack-code-text">
                {line.tokens.map((token, index) => (
                  <span key={`${line.number}-${index}`} data-token={token.tone}>
                    {token.text}
                  </span>
                ))}
              </span>
            </span>
          ))}
        </code>
      </pre>

      <div className="attack-demo-footer">
        {active.chips.map((chip) => (
          <span key={chip}>{chip}</span>
        ))}
      </div>
    </div>
  );
}
