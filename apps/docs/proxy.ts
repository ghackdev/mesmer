import { NextRequest, NextResponse } from 'next/server';
import { isMarkdownPreferred, rewritePath } from 'fumadocs-core/negotiation';
import { blogContentRoute, blogRoute, docsContentRoute, docsRoute } from '@/lib/shared';

const { rewrite: rewriteDocs } = rewritePath(
  `${docsRoute}{/*path}`,
  `${docsContentRoute}{/*path}/content.md`,
);
const { rewrite: rewriteSuffix } = rewritePath(
  `${docsRoute}{/*path}.mdx`,
  `${docsContentRoute}{/*path}/content.md`,
);
const { rewrite: rewriteBlog } = rewritePath(
  `${blogRoute}{/*path}`,
  `${blogContentRoute}{/*path}/content.md`,
);
const { rewrite: rewriteBlogSuffix } = rewritePath(
  `${blogRoute}{/*path}.mdx`,
  `${blogContentRoute}{/*path}/content.md`,
);

export default function proxy(request: NextRequest) {
  const result = rewriteSuffix(request.nextUrl.pathname);
  if (result) {
    return NextResponse.rewrite(new URL(result, request.nextUrl));
  }

  const blogSuffix = rewriteBlogSuffix(request.nextUrl.pathname);
  if (blogSuffix) {
    return NextResponse.rewrite(new URL(blogSuffix, request.nextUrl));
  }

  if (isMarkdownPreferred(request)) {
    const result = rewriteDocs(request.nextUrl.pathname);

    if (result) {
      return NextResponse.rewrite(new URL(result, request.nextUrl));
    }

    const blogResult = rewriteBlog(request.nextUrl.pathname);

    if (blogResult) {
      return NextResponse.rewrite(new URL(blogResult, request.nextUrl));
    }
  }

  return NextResponse.next();
}
