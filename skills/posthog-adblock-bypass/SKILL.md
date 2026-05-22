---
name: posthog-adblock-bypass
description: Configure a Next.js app using posthog-js so session recording and dead-click capture survive browser ad blockers. Aliases the three blocker-flagged JS chunks (dead-clicks-autocapture.js, recorder.js, posthog-recorder.js) to bland same-origin paths via Next.js rewrites, and monkey-patches HTMLScriptElement so posthog-js requests the aliases. TRIGGER when posthog-js session replay or dead-click capture is failing in production with ERR_BLOCKED_BY_CLIENT or 404s on /static/dead-clicks-autocapture.js / /static/recorder.js / /static/posthog-recorder.js, or when the user wants to bypass ad blockers for these specific assets. Works alongside an existing PostHog reverse proxy (managed or otherwise) — only the three blocked files divert through Next.js, all other PostHog traffic stays on the original api_host. SKIP for unrelated PostHog setup, non-Next.js apps, or when capture/decide endpoints (/e/, /decide/, /array/*/config.js) are the ones being blocked — those need a different treatment.
---

# PostHog ad-blocker bypass for Next.js

## When to use this

The user has posthog-js working *mostly* — events, feature flags, decide, config all reach PostHog fine — but **session recording and/or dead-click capture aren't working**, and DevTools shows:

- `/static/dead-clicks-autocapture.js` failing
- `/static/recorder.js` or `/static/posthog-recorder.js` failing
- `ERR_BLOCKED_BY_CLIENT` or a synthesized 404 (the file actually returns 200 via `curl`)

Root cause: ad blockers (uBlock Origin / Brave Shields / AdBlock Plus / EasyPrivacy) match on **filename patterns** (`recorder`, `autocapture`, `dead-clicks`) regardless of host. A reverse proxy alone doesn't help — renaming on a different host still trips the same filter. **Confirmation step**: ask the user to disable their ad blocker on the page; if the requests succeed, this skill applies.

This skill applies the **surgical** fix: only those three files divert through the Next.js app under bland filenames. All other PostHog traffic (events, decide, config, recording uploads) keeps using the existing `api_host`.

## Prerequisites to confirm before implementing

1. The project is **Next.js** (App Router or Pages Router both fine) with `posthog-js` from npm.
2. Server-side: `curl -I https://<api_host>/static/dead-clicks-autocapture.js?v=1.x` returns 200. If it returns 404, the upstream proxy is misconfigured — **fix that first**, this skill won't help.
3. Identify the **PostHog cloud region**: US (`us-assets.i.posthog.com`) or EU (`eu-assets.i.posthog.com`). Default to US if unclear, but ask.
4. Locate the existing `posthog.init(...)` call (commonly `src/lib/posthog.ts`, a provider component, or `app/layout.tsx`). Note the file so you can hook the rewriter before init.
5. **Session replay must be enabled in the PostHog project dashboard** (Settings → Project → Session replay → "Record user sessions"). If it's off, posthog-js never even tries to load the recorder, so this skill produces no visible effect. Surface this check to the user.

## Implementation — three changes

### 1. Add rewrites to `next.config.{ts,js,mjs}`

Insert a `rewrites()` block. Use `/_p/` as the alias prefix (or any path that doesn't contain words like `recorder`, `analytics`, `tracking`, `posthog`).

```ts
import type { NextConfig } from "next";

const PH_ASSETS = "https://us-assets.i.posthog.com"; // EU: "https://eu-assets.i.posthog.com"

const nextConfig: NextConfig = {
  // ...existing config...
  async rewrites() {
    return [
      { source: "/_p/dc.js", destination: `${PH_ASSETS}/static/dead-clicks-autocapture.js` },
      { source: "/_p/r.js",  destination: `${PH_ASSETS}/static/recorder.js` },
      { source: "/_p/r2.js", destination: `${PH_ASSETS}/static/posthog-recorder.js` },
    ];
  },
};

export default nextConfig;
```

Why all three: posthog-js renamed the recorder chunk across versions. Covering both `recorder.js` and `posthog-recorder.js` makes the skill version-resilient. Rewrites preserve the `?v=1.x.y` query string automatically and incur no Node overhead.

If the project already has a `rewrites()` or `redirects()` block, **merge** rather than replace.

### 2. Create the script-tag rewriter

New file at `src/lib/posthog-rewrite-loader.ts` (adjust path to match the repo's lib convention):

```ts
const REWRITES: Array<[RegExp, string]> = [
  [/\/static\/dead-clicks-autocapture\.js/, "/_p/dc.js"],
  [/\/static\/posthog-recorder\.js/,        "/_p/r2.js"],
  [/\/static\/recorder\.js/,                "/_p/r.js"],
];

export function installPostHogScriptRewriter() {
  if (typeof window === "undefined") return;
  const w = window as Window & { __phRewriteInstalled?: boolean };
  if (w.__phRewriteInstalled) return;
  w.__phRewriteInstalled = true;

  const desc = Object.getOwnPropertyDescriptor(HTMLScriptElement.prototype, "src");
  if (!desc?.set || !desc?.get) return;

  Object.defineProperty(HTMLScriptElement.prototype, "src", {
    configurable: true,
    enumerable: true,
    get() {
      return desc.get!.call(this);
    },
    set(value: string) {
      if (typeof value === "string") {
        for (const [pattern, replacement] of REWRITES) {
          if (pattern.test(value)) {
            const qIndex = value.indexOf("?");
            const query = qIndex >= 0 ? value.slice(qIndex) : "";
            value = replacement + query; // strip host -> same-origin
            break;
          }
        }
      }
      desc.set!.call(this, value);
    },
  });
}
```

Notes:
- The `__phRewriteInstalled` flag is required because Next.js dev HMR can re-execute modules and `Object.defineProperty` would otherwise throw.
- Stripping the host (replacing the entire URL with `/_p/dc.js?v=...`) makes the request same-origin, avoiding a CORS preflight on top of the blocker bypass.
- The patcher targets the `src` property setter on the prototype — posthog-js loads chunks by setting `script.src`, so this catches them. It does **not** catch `fetch()` or dynamic `import()` (not used by posthog-js for these chunks today, but worth noting if a future SDK version changes).

### 3. Wire the rewriter to run before `posthog.init`

The patcher must be installed **before** any `posthog.init` call. Module-level code in the same file as `posthog.init` works because module evaluation precedes `useEffect`:

```ts
// src/lib/posthog.ts (or wherever posthog.init lives)
import posthog from "posthog-js";
import { installPostHogScriptRewriter } from "@/lib/posthog-rewrite-loader";

if (typeof window !== "undefined") {
  installPostHogScriptRewriter();
}

export const initPostHog = () => {
  if (typeof window !== "undefined") {
    posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
      api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST, // unchanged
      // ...existing config...
    });
  }
};

export { posthog };
```

If `posthog.init` is called from `<Script strategy="beforeInteractive">` in `app/layout.tsx` instead of from a client module, put the patcher in its own `<Script strategy="beforeInteractive">` block placed **above** the PostHog one. Don't use `afterInteractive` — by then posthog may have already started loading chunks.

## Verification

1. **Server side** — after deploy:
   ```bash
   curl -I "https://<your-domain>/_p/dc.js?v=1.0"
   curl -I "https://<your-domain>/_p/r2.js?v=1.0"
   ```
   Both should return 200, `content-type: text/javascript`. If 404, the rewrite isn't picked up — Next.js needs a rebuild after `next.config` changes.

2. **Browser with ad blocker enabled** — in DevTools Network:
   - Requests to `/_p/dc.js` and `/_p/r2.js` succeed (200).
   - **No** `/static/dead-clicks-autocapture.js` or `/static/posthog-recorder.js` requests visible.
   - In uBlock Origin's Logger, `/_p/*` entries should show `--` (allowed), not red.

3. **PostHog dashboard**:
   - Live Events shows dead-click events firing.
   - Session replay shows recordings (allow ~5 min for ingestion).
   - If recordings still don't appear, the issue is likely the **dashboard toggle** (Settings → Session replay), not this skill.

## Common follow-ups and pitfalls

- **"It still doesn't work after deploy"** — rewrites only take effect after `next build`. Local dev needs `npm run dev` restart. Production needs a redeploy.
- **"A different chunk is now blocked"** — surveys, web-vitals, exception-autocapture. Add a fourth rewrite + a fourth regex entry. Pattern is identical.
- **"Capture endpoints are also blocked"** — `/e/`, `/decide/`, `/array/*/config.js` getting blocked is a different problem (host-level rather than filename-level). Solve with a PostHog reverse proxy on the user's own domain, not this skill. PostHog's docs cover that.
- **"Want to proxy everything through Next.js instead"** — possible but discouraged. Session recording is high-volume (kilobytes per second per active user); routing through Next.js multiplies function invocations 10–100×. The PostHog-managed proxy is purpose-built for this load. Use full-proxy only if you have a hard CSP/compliance requirement.
- **SDK upgrades** — if posthog-js renames a chunk in a future version, the rewriter silently misses it. After upgrades, watch DevTools Network for any `/static/*.js` request leaking through and add a regex entry.
- **Network-level blockers** (Pi-hole / NextDNS) blocking by domain are not bypassed by this. They're a much smaller cohort than browser extensions and your own domain isn't on their lists.

## Files modified summary (template for the PR description)

| File | Change |
|---|---|
| `next.config.{ts,js}` | Add `rewrites()` for `/_p/dc.js`, `/_p/r.js`, `/_p/r2.js` |
| `src/lib/posthog-rewrite-loader.ts` | New — patches `HTMLScriptElement.prototype.src` |
| `src/lib/posthog.ts` (or equivalent) | Call `installPostHogScriptRewriter()` at module load |
