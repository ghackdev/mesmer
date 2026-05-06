import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const routes = [
  { path: '/', include: '#mesmer-home' },
  { path: '/docs', include: '[data-testid="docs-content"]' },
  { path: '/blog', include: 'main' },
  { path: '/blog/introducing-mesmer', include: 'article' },
];

for (const route of routes) {
  test(`${route.path} renders without accessibility violations`, async ({ page }) => {
    await page.goto(route.path);
    await expect(page.locator(route.include).first()).toBeVisible();

    const accessibilityScanResults = await new AxeBuilder({ page }).include(route.include).analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
  });
}

test('LLM, SEO, and install utility routes are available', async ({ request }) => {
  for (const route of [
    '/llms.txt',
    '/llms-full.txt',
    '/sitemap.xml',
    '/robots.txt',
    '/blog/rss.xml',
    '/manifest.webmanifest',
    '/favicon-32x32.png',
    '/apple-touch-icon.png',
    '/icons/android-chrome-192x192.png',
    '/icons/android-chrome-512x512.png',
    '/icons/maskable-icon-512x512.png',
  ]) {
    const response = await request.get(route);
    expect(response.ok()).toBe(true);
  }
});
