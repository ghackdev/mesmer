'use client';

import { useEffect, useRef } from 'react';

type NodeKind = 'safe' | 'vulnerable';

type GlobeNode = {
  x: number;
  y: number;
  z: number;
  kind: NodeKind;
  size: number;
  phase: number;
  label?: string;
};

type ProjectedNode = GlobeNode & {
  sx: number;
  sy: number;
  depth: number;
  scale: number;
};

type VulnerableTrace = {
  id: string;
  points: GlobeNode[];
};

type TraceLabel = {
  node: ProjectedNode;
  alpha: number;
};

const TRACE_CYCLE_FRAMES = 132;
const TRACE_SPAWN_FRAMES = 12;
const TRACE_TRAVERSE_FRAMES = 72;
const TRACE_HOLD_FRAMES = 18;
const TRACE_FADE_FRAMES = TRACE_CYCLE_FRAMES - TRACE_SPAWN_FRAMES - TRACE_TRAVERSE_FRAMES - TRACE_HOLD_FRAMES;

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

const safeNodes: GlobeNode[] = Array.from({ length: 74 }, (_, index) => {
  const offset = 2 / 74;
  const y = index * offset - 1 + offset / 2;
  const radius = Math.sqrt(1 - y * y);
  const angle = index * Math.PI * (3 - Math.sqrt(5));
  const label =
    {
      5: 'refusal',
      13: 'boundary held',
      16: 'clarify',
      28: 'policy',
      37: 'ask permission',
      43: 'safe answer',
      52: 'sanitize',
      57: 'redirect',
      68: 'benign',
    }[index] ?? undefined;

  return {
    x: Math.cos(angle) * radius,
    y,
    z: Math.sin(angle) * radius,
    kind: 'safe',
    size: index % 9 === 0 ? 2.4 : 1.75,
    phase: index * 0.73,
    label,
  };
});

function tracePoint(angle: number, y: number, phase: number, label?: string, size = 2.45): GlobeNode {
  const radius = Math.sqrt(Math.max(0.18, 1 - y * y));

  return {
    x: Math.cos(angle) * radius * 0.92,
    y,
    z: Math.sin(angle) * radius * 0.92,
    kind: 'vulnerable',
    size,
    phase,
    label,
  };
}

const vulnerableTraces: VulnerableTrace[] = [
  {
    id: 'persona-shift',
    points: [
      tracePoint(-1.08, -0.36, 10, 'persona shift'),
      tracePoint(-0.78, -0.12, 10.91),
      tracePoint(-0.48, 0.05, 11.82, 'authority mimic'),
      tracePoint(-0.18, 0.16, 12.73),
      tracePoint(0.16, 0.14, 13.64, 'constraint gap'),
      tracePoint(0.46, -0.02, 14.55),
      tracePoint(0.74, -0.2, 15.46, 'jailbreak path', 3.15),
    ],
  },
  {
    id: 'role-confusion',
    points: [
      tracePoint(-0.66, 0.34, 16.2, 'role confusion'),
      tracePoint(-0.34, 0.24, 17.01),
      tracePoint(-0.02, 0.05, 17.82, 'policy gap'),
      tracePoint(0.27, -0.1, 18.63),
      tracePoint(0.57, -0.2, 19.44, 'hidden request'),
      tracePoint(0.91, -0.34, 20.25, 'leak branch', 3.05),
    ],
  },
  {
    id: 'format-trap',
    points: [
      tracePoint(-0.86, -0.52, 21.3, 'format trap'),
      tracePoint(-0.52, -0.34, 22.11),
      tracePoint(-0.18, -0.13, 22.92, 'evaluator miss'),
      tracePoint(0.18, 0.04, 23.73),
      tracePoint(0.55, 0.18, 24.54, 'unsafe continuation', 3.05),
    ],
  },
];

const nodes = safeNodes;

const safeEdges = safeNodes.flatMap((_, index) => {
  if (index % 3 !== 0) return [];
  return [
    [index, (index + 13) % safeNodes.length],
    [index, (index + 29) % safeNodes.length],
  ] as const;
});

function projectNode(node: GlobeNode, angle: number, width: number, height: number, time: number): ProjectedNode {
  const driftX = Math.sin(time * 0.011 + node.phase) * 0.045 + Math.cos(time * 0.006 + node.phase * 0.47) * 0.018;
  const driftY = Math.cos(time * 0.009 + node.phase * 1.23) * 0.038 + Math.sin(time * 0.005 + node.phase * 0.71) * 0.014;
  const driftZ = Math.sin(time * 0.01 + node.phase * 0.81) * 0.04 + Math.cos(time * 0.004 + node.phase * 1.41) * 0.016;
  const cosY = Math.cos(angle);
  const sinY = Math.sin(angle);
  const cosX = Math.cos(-0.34);
  const sinX = Math.sin(-0.34);
  const sourceX = node.x + driftX;
  const sourceY = node.y + driftY;
  const sourceZ = node.z + driftZ;
  const x = sourceX * cosY + sourceZ * sinY;
  const z = -sourceX * sinY + sourceZ * cosY;
  const y = sourceY * cosX - z * sinX;
  const depth = node.y * sinX + z * cosX;
  const perspective = 2.85;
  const scale = perspective / (perspective - depth);
  const radius = Math.min(width, height) * 0.39;

  return {
    ...node,
    sx: width / 2 + x * radius * scale,
    sy: height / 2 + y * radius * scale,
    depth,
    scale,
  };
}

function drawNodeLabel(
  context: CanvasRenderingContext2D,
  node: ProjectedNode,
  centerX: number,
  centerY: number,
  radius: number,
  alphaMultiplier = 1,
) {
  if (!node.label || node.depth < -0.38) return;

  const isVulnerable = node.kind === 'vulnerable';
  if (!isVulnerable && node.depth < -0.05) return;

  const canvas = context.canvas;
  const rect = canvas.getBoundingClientRect();
  const width = rect.width;

  const frontAlpha = Math.min(0.92, Math.max(0.42, (node.depth + 1.15) / 2));
  const alpha = (isVulnerable ? frontAlpha : Math.min(0.34, Math.max(0.12, frontAlpha * 0.36))) * alphaMultiplier;
  if (alpha < 0.04) return;

  const label = node.label;
  context.save();
  context.font = `${width < 520 ? 9 : 10}px "JetBrains Mono", ui-monospace, SFMono-Regular, Consolas, monospace`;
  const textWidth = context.measureText(label).width;
  const preferredX = node.sx + (isVulnerable ? 12 : 10);
  const x = clamp(preferredX, centerX - radius + 8, centerX + radius - textWidth - 8);
  const y = clamp(node.sy - 7, centerY - radius + 12, centerY + radius - 8);
  context.shadowColor = isVulnerable ? `rgba(214, 64, 72, ${alpha * 0.5})` : `rgba(6, 115, 107, ${alpha * 0.42})`;
  context.shadowBlur = 8;
  context.fillStyle = isVulnerable ? `rgba(141, 31, 38, ${alpha})` : `rgba(6, 115, 107, ${alpha})`;
  context.fillText(label, x, y);
  context.restore();
}

function getTraceProgress(frame: number, edgeCount: number, reducedMotion: boolean) {
  if (reducedMotion) {
    return { alpha: 0.48, segmentPosition: edgeCount };
  }

  const cycleFrame = frame % TRACE_CYCLE_FRAMES;
  if (cycleFrame < TRACE_SPAWN_FRAMES) {
    return { alpha: 0.86 * (cycleFrame / TRACE_SPAWN_FRAMES), segmentPosition: 0 };
  }

  if (cycleFrame < TRACE_SPAWN_FRAMES + TRACE_TRAVERSE_FRAMES) {
    const progress = (cycleFrame - TRACE_SPAWN_FRAMES) / TRACE_TRAVERSE_FRAMES;
    return { alpha: 0.86, segmentPosition: progress * edgeCount };
  }

  if (cycleFrame < TRACE_SPAWN_FRAMES + TRACE_TRAVERSE_FRAMES + TRACE_HOLD_FRAMES) {
    return { alpha: 0.78, segmentPosition: edgeCount };
  }

  const fadeFrame = cycleFrame - TRACE_SPAWN_FRAMES - TRACE_TRAVERSE_FRAMES - TRACE_HOLD_FRAMES;
  return { alpha: 0.78 * (1 - fadeFrame / TRACE_FADE_FRAMES), segmentPosition: edgeCount };
}

function drawActiveTrace(context: CanvasRenderingContext2D, projectedTrace: ProjectedNode[], frame: number, reducedMotion: boolean): TraceLabel[] {
  const edgeCount = projectedTrace.length - 1;
  const { alpha, segmentPosition } = getTraceProgress(frame, edgeCount, reducedMotion);
  const labels: TraceLabel[] = [];

  if (alpha <= 0) return labels;

  context.save();
  context.shadowColor = `rgba(214, 64, 72, ${alpha * 0.5})`;
  context.shadowBlur = 9;

  for (let edgeIndex = 0; edgeIndex < edgeCount; edgeIndex += 1) {
    const edgeVisibility = clamp(segmentPosition - edgeIndex, 0, 1);
    if (edgeVisibility <= 0) continue;

    const a = projectedTrace[edgeIndex];
    const b = projectedTrace[edgeIndex + 1];
    const depthAlpha = Math.max(0.22, Math.min(0.86, (a.depth + b.depth + 2.4) / 4.8));
    const endX = a.sx + (b.sx - a.sx) * edgeVisibility;
    const endY = a.sy + (b.sy - a.sy) * edgeVisibility;

    context.strokeStyle = `rgba(214, 64, 72, ${alpha * edgeVisibility * depthAlpha})`;
    context.lineWidth = 1.7 + edgeVisibility * 0.4;
    context.beginPath();
    context.moveTo(a.sx, a.sy);
    context.lineTo(endX, endY);
    context.stroke();
  }

  for (let index = 0; index < projectedTrace.length; index += 1) {
    const node = projectedTrace[index];
    const pointVisibility = index === 0 ? 1 : clamp(segmentPosition - index + 1, 0, 1);
    const front = (node.depth + 1) / 2;
    const pointAlpha = alpha * pointVisibility * (0.5 + front * 0.42);
    if (pointAlpha <= 0.04) continue;

    const size = node.size * node.scale * 2.25;
    context.fillStyle = `rgba(214, 64, 72, ${pointAlpha})`;
    context.beginPath();
    context.arc(node.sx, node.sy, size, 0, Math.PI * 2);
    context.fill();

    context.strokeStyle = `rgba(214, 64, 72, ${Math.min(0.72, pointAlpha)})`;
    context.lineWidth = 1.1;
    context.beginPath();
    context.arc(node.sx, node.sy, size + 4.2, 0, Math.PI * 2);
    context.stroke();

    if (node.label) {
      labels.push({ node, alpha: pointAlpha });
    }
  }

  context.restore();
  return labels;
}

function drawGlobe(canvas: HTMLCanvasElement, angle: number, time: number, activeTrace: VulnerableTrace, reducedMotion: boolean) {
  const context = canvas.getContext('2d');
  if (!context) return;

  const rect = canvas.getBoundingClientRect();
  const ratio = canvas.width / Math.max(1, rect.width);
  const width = rect.width;
  const height = rect.height;
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  const projected = nodes.map((node) => projectNode(node, angle, width, height, time));
  const projectedTrace = activeTrace.points.map((node) => projectNode(node, angle, width, height, time));
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) * 0.39;

  context.clearRect(0, 0, width, height);
  context.save();
  context.lineCap = 'round';

  context.strokeStyle = 'rgba(6, 115, 107, 0.16)';
  context.lineWidth = 1;
  for (let ring = 0; ring < 3; ring += 1) {
    context.beginPath();
    context.ellipse(centerX, centerY, radius * (0.72 + ring * 0.19), radius * 0.28, angle * 0.36 + ring * 0.8, 0, Math.PI * 2);
    context.stroke();
  }

  for (const [start, end] of safeEdges) {
    const a = projected[start];
    const b = projected[end];
    const alpha = Math.max(0.08, Math.min(0.32, (a.depth + b.depth + 2) / 8));
    context.strokeStyle = `rgba(6, 115, 107, ${alpha})`;
    context.lineWidth = 1;
    context.beginPath();
    context.moveTo(a.sx, a.sy);
    context.lineTo(b.sx, b.sy);
    context.stroke();
  }

  for (const node of [...projected].sort((a, b) => a.depth - b.depth)) {
    const front = (node.depth + 1) / 2;
    const alpha = 0.26 + front * 0.52;
    const size = node.size * node.scale * 1.9;

    context.fillStyle = `rgba(6, 115, 107, ${alpha})`;
    context.beginPath();
    context.arc(node.sx, node.sy, size, 0, Math.PI * 2);
    context.fill();
  }

  const traceLabels = drawActiveTrace(context, projectedTrace, time, reducedMotion);
  const safeLabelCandidates = projected
    .filter((node) => node.label && node.depth >= -0.05)
    .sort((a, b) => b.depth - a.depth);
  const safeLabels = width < 520 ? safeLabelCandidates.slice(0, 2) : safeLabelCandidates;

  for (const node of safeLabels) {
    drawNodeLabel(context, node, centerX, centerY, radius);
  }

  for (const { node, alpha } of traceLabels) {
    drawNodeLabel(context, node, centerX, centerY, radius, alpha);
  }

  context.restore();
}

export function EmbeddingGlobe() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    let frame = 0;
    let animationFrame = 0;
    let reducedMotion = mediaQuery.matches;
    let traceIndex = Math.floor(Math.random() * vulnerableTraces.length);
    let traceCycle = -1;

    const getActiveTrace = () => {
      if (reducedMotion) return vulnerableTraces[0];

      const nextCycle = Math.floor(frame / TRACE_CYCLE_FRAMES);
      if (nextCycle !== traceCycle) {
        traceCycle = nextCycle;
        const nextIndex = Math.floor(Math.random() * vulnerableTraces.length);
        traceIndex = nextIndex === traceIndex ? (nextIndex + 1) % vulnerableTraces.length : nextIndex;
      }

      return vulnerableTraces[traceIndex];
    };

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const scale = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.max(1, Math.floor(rect.width * scale));
      canvas.height = Math.max(1, Math.floor(rect.height * scale));
      drawGlobe(canvas, reducedMotion ? 0.72 : frame * 0.006, frame, getActiveTrace(), reducedMotion);
    };

    const render = () => {
      frame += 1;
      drawGlobe(canvas, frame * 0.006, frame, getActiveTrace(), reducedMotion);
      animationFrame = window.requestAnimationFrame(render);
    };

    const onMotionChange = (event: MediaQueryListEvent) => {
      reducedMotion = event.matches;
      window.cancelAnimationFrame(animationFrame);
      if (reducedMotion) {
        drawGlobe(canvas, 0.72, 0, getActiveTrace(), true);
      } else {
        animationFrame = window.requestAnimationFrame(render);
      }
    };

    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(canvas);
    mediaQuery.addEventListener('change', onMotionChange);
    resize();

    if (!reducedMotion) {
      animationFrame = window.requestAnimationFrame(render);
    }

    return () => {
      window.cancelAnimationFrame(animationFrame);
      resizeObserver.disconnect();
      mediaQuery.removeEventListener('change', onMotionChange);
    };
  }, []);

  return (
    <div className="embedding-globe" aria-label="Rotating embedding network with safe and vulnerable paths" role="img">
      <canvas ref={canvasRef} aria-hidden="true" className="embedding-globe-canvas" />
    </div>
  );
}
