import { appName, appTagline } from '@/lib/shared';
import { ImageResponse } from 'next/og';

export const revalidate = false;

export function GET() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          background: '#02070d',
          color: '#d8fff7',
          padding: 72,
          fontFamily: 'monospace',
        }}
      >
        <div style={{ color: '#2dd5c3', fontSize: 28, marginBottom: 32 }}>authorized safety research harness</div>
        <div style={{ fontSize: 96, fontWeight: 700, letterSpacing: 0 }}>{appName}</div>
        <div style={{ marginTop: 24, maxWidth: 900, fontSize: 36, lineHeight: 1.35, color: '#86aab0' }}>{appTagline}</div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
    },
  );
}
