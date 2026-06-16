---
name: nextjs
description: Next.js project rules. Read this when you create or edit a Next.js app. Covers Next.js 16+ conventions (proxy.ts, app router), Node version, common foot-guns, and the Pi-agent-compatible setup.
license: MIT
---

# Next.js skill

Read this when starting any task in a Next.js project — `app/`, `pages/`, `next.config.*`, or `package.json` declares `"next"`.

## Pinned versions (Pi-agent setup)

- **Next.js**: `16.2.x` minimum. Earlier than 16 lacks the `proxy` file convention and several App Router fixes Pi relies on. Use `^16.2.0` in `package.json`.
- **Node**: `22.19+` (snapshot ships Node 22 LTS). Lower versions break Next 16 type emit.
- **React / React DOM**: `19.x`. Don't pin to 18 — Next 16 expects React 19 server-action types.
- **TypeScript**: `5.6+`. Older versions can't infer App Router segment params.

If you bootstrap a new project, use:

```json
{
  "dependencies": {
    "next": "^16.2.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "typescript": "^5.6.0"
  }
}
```

## The `middleware` → `proxy` rename (Next.js 16.2)

Next.js 16.2 deprecated the `middleware` file convention. **Use `proxy.ts`** instead.

```ts
// ❌ DON'T — deprecated, breaks build in 16.2+
// web/src/middleware.ts
export function middleware(request: NextRequest) { ... }

// ✅ DO — Next.js 16.2 convention
// web/src/proxy.ts
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  // ...
  return NextResponse.next();
}

export const config = {
  matcher: ["/admin/:path*"],
};
```

- Function name: `proxy` (not `middleware`)
- File name: `proxy.ts` (not `middleware.ts`)
- Same `NextRequest` / `NextResponse` API otherwise

Having both `middleware.ts` AND `proxy.ts` is a build error. Pick one — proxy.

## Don't proxy via `next.config rewrites` if you use `trailingSlash: false`

`next.config.{ts,js} rewrites` runs **after** URL normalization. With `trailingSlash: false`, trailing slashes get stripped first → your rewrite never matches → redirect loop.

```ts
// ❌ DOESN'T WORK with trailingSlash:false — redirect loop
// next.config.ts
const config = {
  trailingSlash: false,
  async rewrites() {
    return [{ source: "/generator/:path*", destination: "https://other.app/:path*" }];
  },
};

// ✅ Use proxy.ts — runs BEFORE URL normalization
// src/proxy.ts
export function proxy(request: NextRequest) {
  if (request.nextUrl.pathname.startsWith("/generator/")) {
    const target = new URL(request.nextUrl.pathname.replace("/generator", ""), "https://other.app");
    return NextResponse.rewrite(target);
  }
  return NextResponse.next();
}
```

## For SEO routes: `fetch + new NextResponse(body)` beats `NextResponse.rewrite`

`NextResponse.rewrite()` performs an internal redirect — some SEO crawlers see a 302 chain. For routes that need to be indexed by their public URL (like `/generator/some-page`), fetch the target server-side and stream the HTML.

```ts
// src/proxy.ts — SEO-safe proxy
export async function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  if (!pathname.startsWith("/generator/")) return NextResponse.next();

  const targetUrl = `https://other.app${pathname.replace("/generator", "")}${search}`;
  const upstream = await fetch(targetUrl, {
    headers: request.headers,
    redirect: "manual",
  });
  // Stream body + preserve content-type / cache headers
  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: upstream.headers,
  });
}
```

## App Router conventions (Next.js 16)

- `app/layout.tsx` is required at root (not `pages/_app.tsx`)
- `metadata` is exported from `layout.tsx` / `page.tsx`, not `<Head>`
- Server components by default — add `"use client"` only when you need state/effects
- Route handlers: `app/api/foo/route.ts` exporting `GET` / `POST` etc.
- Dynamic segments: `app/[slug]/page.tsx` with `params: Promise<{ slug: string }>` (Next 16 wraps params in Promise — `await params` first)

## Things to NOT do

- ❌ Don't use `pages/` router for new projects — App Router is the default and Pi expects it
- ❌ Don't add `next-env.d.ts` manually — Next.js generates it; just `.gitignore` if needed
- ❌ Don't pin `"next": "@latest"` or `"next": "16"` — be explicit: `"^16.2.0"`
- ❌ Don't use `type="module"` in HTML script tags for inline Next.js fixtures — breaks hydration
- ❌ Don't import from `next/dist/*` — internal API, breaks across versions
- ❌ Don't use `getServerSideProps` / `getStaticProps` in App Router — use server components + `fetch` with `next: { revalidate: ... }`

## Bootstrap quickstart

```bash
npx create-next-app@^16.2.0 my-app \
  --typescript --eslint --tailwind --app --src-dir \
  --no-import-alias
cd my-app
npm install
npm run dev
```

This produces a 16.2-compliant skeleton with App Router, TypeScript, Tailwind, and `src/` layout. Add `src/proxy.ts` if you need redirects/rewrites.

## Common error messages and fixes

| Error | Cause | Fix |
|---|---|---|
| `Module not found: next/server` | Old Next or wrong import path | `import { NextResponse } from "next/server"` (singular `server`) |
| `Duplicate middleware/proxy file` | Both `middleware.ts` and `proxy.ts` exist | Delete `middleware.ts`, keep `proxy.ts` |
| Redirect loop on `/some-path/` | `trailingSlash:false` + `next.config rewrites` | Move logic to `proxy.ts` |
| `params is not iterable` or `params.slug undefined` | Next 16 wraps params in Promise | `const { slug } = await params;` |
| `Hydration mismatch` on a server component | Touched `window` / `document` in render | Add `"use client"` or guard with `typeof window !== 'undefined'` |
| `Cannot find module 'next-env.d.ts'` | Path moved in 16.2 | Regenerate with `npm run build` once; or `npx next types` |

## When NOT to use this skill

- The project's `package.json` has no `next` dependency
- User wants a static HTML artifact (no Next.js needed) — use the main design-agent skill directly
- User explicitly asks for `pages/` router or older Next version — follow their lead, but warn it's deprecated
