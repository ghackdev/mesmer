import { RootProvider } from 'fumadocs-ui/provider/next';
import './global.css';
import { i18nUI } from '@/lib/layout.shared';
import { createMetadata } from '@/lib/seo/metadata';
import { appName, siteUrl } from '@/lib/shared';

export const metadata = createMetadata();

export default function Layout({ children }: LayoutProps<'/'>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta name="application-name" content={appName} />
        <meta name="apple-mobile-web-app-title" content={appName} />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="theme-color" content="#071425" />
        <link rel="alternate" type="application/rss+xml" title={`${appName} Blog`} href={`${siteUrl}/blog/rss.xml`} />
      </head>
      <body className="flex flex-col min-h-screen">
        <RootProvider i18n={i18nUI.provider('en')}>{children}</RootProvider>
      </body>
    </html>
  );
}
