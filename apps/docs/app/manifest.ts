import type { MetadataRoute } from 'next';
import { appName, appTagline, siteUrl } from '@/lib/shared';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: `${appName} Documentation`,
    short_name: appName,
    description: appTagline,
    id: '/',
    start_url: '/',
    scope: '/',
    display: 'standalone',
    display_override: ['window-controls-overlay', 'standalone', 'browser'],
    background_color: '#02070d',
    theme_color: '#071425',
    categories: ['developer', 'productivity', 'security'],
    lang: 'en',
    dir: 'ltr',
    icons: [
      {
        src: '/icons/favicon-48x48.png',
        sizes: '48x48',
        type: 'image/png',
      },
      {
        src: '/icons/favicon-96x96.png',
        sizes: '96x96',
        type: 'image/png',
      },
      {
        src: '/icons/apple-touch-icon.png',
        sizes: '180x180',
        type: 'image/png',
      },
      {
        src: '/icons/android-chrome-192x192.png',
        sizes: '192x192',
        type: 'image/png',
        purpose: 'any',
      },
      {
        src: '/icons/icon-256x256.png',
        sizes: '256x256',
        type: 'image/png',
        purpose: 'any',
      },
      {
        src: '/icons/icon-384x384.png',
        sizes: '384x384',
        type: 'image/png',
        purpose: 'any',
      },
      {
        src: '/icons/android-chrome-512x512.png',
        sizes: '512x512',
        type: 'image/png',
        purpose: 'any',
      },
      {
        src: '/icons/maskable-icon-512x512.png',
        sizes: '512x512',
        type: 'image/png',
        purpose: 'maskable',
      },
    ],
    screenshots: [
      {
        src: `${siteUrl}/og.png`,
        sizes: '1200x630',
        type: 'image/png',
        form_factor: 'wide',
      },
    ],
  };
}
