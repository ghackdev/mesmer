import type { Metadata } from 'next';
import { appName, appTagline, siteUrl } from '@/lib/shared';

export function absoluteUrl(path = '/') {
  return new URL(path, siteUrl).toString();
}

export function createMetadata({
  title,
  description = appTagline,
  path = '/',
  image = '/og.png',
  type = 'website',
}: {
  title?: string;
  description?: string;
  path?: string;
  image?: string;
  type?: 'website' | 'article';
} = {}): Metadata {
  const resolvedTitle = title ? `${title} | ${appName}` : `${appName} | ${appTagline}`;
  const url = absoluteUrl(path);
  const imageUrl = image.startsWith('http') ? image : absoluteUrl(image);

  return {
    applicationName: appName,
    title: resolvedTitle,
    description,
    manifest: '/manifest.webmanifest',
    appleWebApp: {
      capable: true,
      title: appName,
      statusBarStyle: 'black-translucent',
    },
    formatDetection: {
      telephone: false,
    },
    icons: {
      icon: [
        { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
        { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
        { url: '/favicon-96x96.png', sizes: '96x96', type: 'image/png' },
        { url: '/icons/favicon-48x48.png', sizes: '48x48', type: 'image/png' },
      ],
      shortcut: [{ url: '/favicon-32x32.png', type: 'image/png' }],
      apple: [{ url: '/apple-touch-icon.png', sizes: '180x180', type: 'image/png' }],
      other: [
        {
          rel: 'mask-icon',
          url: '/icons/maskable-icon-512x512.png',
          color: '#2dd5c3',
        },
      ],
    },
    alternates: {
      canonical: url,
    },
    openGraph: {
      type,
      title: resolvedTitle,
      description,
      url,
      siteName: appName,
      images: [
        {
          url: imageUrl,
          width: 1200,
          height: 630,
          alt: resolvedTitle,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title: resolvedTitle,
      description,
      images: [imageUrl],
    },
  };
}
