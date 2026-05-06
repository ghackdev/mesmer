# Mesmer Docs

Next.js documentation, landing, and blog app for Mesmer.

This app is scaffolded from the Fumadocs Next.js MDX template and uses Fumadocs UI, Tailwind CSS, and small local shadcn-style UI components.

## Development

Run from the repository root:

```bash
pnpm docs:dev
```

Or run from this package:

```bash
pnpm dev
```

The local preview normally runs on `http://localhost:3000`; use another port when that is already occupied.

## Content

- Documentation: `content/docs/en`
- Blog posts: `content/blog/en`
- Default English URLs are hidden: `/docs`, `/blog`, and `/blog/<slug>`

## Checks

```bash
pnpm typecheck
pnpm lint
pnpm build
pnpm test:e2e
```

LLM and SEO routes include `/llms.txt`, `/llms-full.txt`, `/sitemap.xml`, `/robots.txt`, `/blog/rss.xml`, and `.mdx` markdown mirrors for docs and blog pages.
