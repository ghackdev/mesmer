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

const safeNodes: GlobeNode[] = Array.from({ length: 74 }, (_, index) => {
  const offset = 2 / 74;
  const y = index * offset - 1 + offset / 2;
  const radius = Math.sqrt(1 - y * y);
  const angle = index * Math.PI * (3 - Math.sqrt(5));
  const label =
    {
      5: 'refusal',
      16: 'clarify',
      28: 'policy',
      43: 'safe answer',
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

const vulnerableNodes: GlobeNode[] = Array.from({ length: 12 }, (_, index) => {
  const t = index / 11;
  const angle = -0.95 + t * 1.72;
  const y = -0.42 + Math.sin(t * Math.PI) * 0.54;
  const radius = Math.sqrt(Math.max(0.18, 1 - y * y));

  return {
    x: Math.cos(angle) * radius * 0.92,
    y,
    z: Math.sin(angle) * radius * 0.92,
    kind: 'vulnerable',
    size: index === 7 ? 3.2 : 2.45,
    phase: 10 + index * 0.91,
    label:
      {
        1: 'persona shift',
        4: 'constraint gap',
        7: 'jailbreak path',
        10: 'leak branch',
      }[index] ?? undefined,
  };
});

const nodes = [...safeNodes, ...vulnerableNodes];

const safeEdges = safeNodes.flatMap((_, index) => {
  if (index % 3 !== 0) return [];
  return [
    [index, (index + 13) % safeNodes.length],
    [index, (index + 29) % safeNodes.length],
  ] as const;
});

const vulnerableOffset = safeNodes.length;
const vulnerableEdges = vulnerableNodes.slice(1).map((_, index) => [vulnerableOffset + index, vulnerableOffset + index + 1] as const);

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

function drawNodeLabel(context: CanvasRenderingContext2D, node: ProjectedNode) {
  if (!node.label || node.depth < -0.38) return;

  const isVulnerable = node.kind === 'vulnerable';
  const canvas = context.canvas;
  const rect = canvas.getBoundingClientRect();
  const width = rect.width;
  if (width < 520 && !isVulnerable) return;

  const alpha = Math.min(0.92, Math.max(0.42, (node.depth + 1.15) / 2));
  const label = node.label;
  context.save();
  context.font = `${width < 520 ? 9 : 10}px "JetBrains Mono", ui-monospace, SFMono-Regular, Consolas, monospace`;
  const textWidth = context.measureText(label).width;
  const preferredX = node.sx + (isVulnerable ? 12 : 10);
  const x = Math.min(Math.max(preferredX, 8), width - textWidth - 8);
  const y = node.sy - 7;
  context.shadowColor = isVulnerable ? `rgba(214, 64, 72, ${alpha * 0.5})` : `rgba(6, 115, 107, ${alpha * 0.42})`;
  context.shadowBlur = 8;
  context.fillStyle = isVulnerable ? `rgba(141, 31, 38, ${alpha})` : `rgba(6, 115, 107, ${alpha})`;
  context.fillText(label, x, y);
  context.restore();
}

function drawGlobe(canvas: HTMLCanvasElement, angle: number, time: number) {
  const context = canvas.getContext('2d');
  if (!context) return;

  const rect = canvas.getBoundingClientRect();
  const ratio = canvas.width / Math.max(1, rect.width);
  const width = rect.width;
  const height = rect.height;
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  const projected = nodes.map((node) => projectNode(node, angle, width, height, time));
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

  for (const [start, end] of vulnerableEdges) {
    const a = projected[start];
    const b = projected[end];
    const alpha = Math.max(0.28, Math.min(0.72, (a.depth + b.depth + 2.4) / 4.8));
    context.strokeStyle = `rgba(214, 64, 72, ${alpha})`;
    context.lineWidth = 1.8;
    context.beginPath();
    context.moveTo(a.sx, a.sy);
    context.lineTo(b.sx, b.sy);
    context.stroke();
  }

  for (const node of [...projected].sort((a, b) => a.depth - b.depth)) {
    const front = (node.depth + 1) / 2;
    const alpha = node.kind === 'safe' ? 0.26 + front * 0.52 : 0.5 + front * 0.42;
    const color = node.kind === 'safe' ? '6, 115, 107' : '214, 64, 72';
    const size = node.size * node.scale * (node.kind === 'safe' ? 1.9 : 2.25);

    context.fillStyle = `rgba(${color}, ${alpha})`;
    context.beginPath();
    context.arc(node.sx, node.sy, size, 0, Math.PI * 2);
    context.fill();

    if (node.kind === 'vulnerable') {
      context.strokeStyle = `rgba(${color}, ${Math.min(0.72, alpha)})`;
      context.lineWidth = 1.1;
      context.beginPath();
      context.arc(node.sx, node.sy, size + 4.2, 0, Math.PI * 2);
      context.stroke();
    }
  }

  for (const node of projected) {
    drawNodeLabel(context, node);
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

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const scale = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.max(1, Math.floor(rect.width * scale));
      canvas.height = Math.max(1, Math.floor(rect.height * scale));
      drawGlobe(canvas, reducedMotion ? 0.72 : frame * 0.006, frame);
    };

    const render = () => {
      frame += 1;
      drawGlobe(canvas, frame * 0.006, frame);
      animationFrame = window.requestAnimationFrame(render);
    };

    const onMotionChange = (event: MediaQueryListEvent) => {
      reducedMotion = event.matches;
      window.cancelAnimationFrame(animationFrame);
      if (reducedMotion) {
        drawGlobe(canvas, 0.72, 0);
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
