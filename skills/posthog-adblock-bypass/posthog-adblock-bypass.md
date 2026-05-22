# PostHog session recording + dead-click capture: ad-blocker bypass via Next.js

## The problem

Your PostHog proxy at `api.agentruntime.app` works for everything except these files (US cloud):

- `/static/dead-clicks-autocapture.js`
- `/static/posthog-recorder.js` (and the older `/static/recorder.js` name)

`curl` returns `200` for both, so the proxy is fine. The "404" in DevTools is **synthesized by the user's ad blocker** (uBlock Origin / Brave Shields / AdBlock Plus). EasyPrivacy and similar lists match on the **filename pattern** (`recorder`, `autocapture`, `dead-clicks`) regardless of host — so renaming on a different host won't help on its own.

You can't change `api.agentruntime.app` (managed by PostHog). Two options:

- **A. Surgical proxy (recommended).** Keep `api.agentruntime.app` for everything else. Only the three blocker-flagged JS files get aliased through your Next.js app under bland filenames.
- **B. Full proxy through Next.js.** Move *all* PostHog traffic (events, decide, recordings, static, everything) through your Next.js app and drop `api.agentruntime.app` from the SDK config.

A monkey-patch in posthog-js rewrites the lazy-loaded `<script>` URLs so they hit the aliased paths instead of the blocker-flagged ones.

---

## Approach A — Surgical proxy (recommended)

Only the three blocker-flagged files go through Next.js. Everything else (`/array/*/config.js`, `/e/`, `/s/`, `/decide/`, `/i/v0/*`, etc.) keeps using `api.agentruntime.app`.

### A.1 — `next.config.js` rewrites

```js
// next.config.js
const PH_ASSETS = 'https://us-assets.i.posthog.com'; // US cloud

module.exports = {
  async rewrites() {
    return [
      { source: '/_p/dc.js', destination: `${PH_ASSETS}/static/dead-clicks-autocapture.js` },
      { source: '/_p/r.js',  destination: `${PH_ASSETS}/static/recorder.js` },
      { source: '/_p/r2.js', destination: `${PH_ASSETS}/static/posthog-recorder.js` },
    ];
  },
};
```

The path prefix `/_p/` is arbitrary — anything bland works. Rewrites are edge-level, preserve query strings (`?v=1.372.10`), and add no Node overhead.

### A.2 — `lib/posthog-rewrite-loader.ts`

```ts
const REWRITES: Array<[RegExp, string]> = [
  [/\/static\/dead-clicks-autocapture\.js/, '/_p/dc.js'],
  [/\/static\/posthog-recorder\.js/,        '/_p/r2.js'],
  [/\/static\/recorder\.js/,                '/_p/r.js'],
];

export function installPostHogScriptRewriter() {
  if (typeof window === 'undefined') return;
  if ((window as any).__phRewriteInstalled) return;
  (window as any).__phRewriteInstalled = true;

  const desc = Object.getOwnPropertyDescriptor(HTMLScriptElement.prototype, 'src');
  if (!desc?.set || !desc?.get) return;

  Object.defineProperty(HTMLScriptElement.prototype, 'src', {
    configurable: true,
    enumerable: true,
    get() { return desc.get!.call(this); },
    set(value: string) {
      if (typeof value === 'string') {
        for (const [pattern, replacement] of REWRITES) {
          if (pattern.test(value)) {
            const qIndex = value.indexOf('?');
            const query = qIndex >= 0 ? value.slice(qIndex) : '';
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

### A.3 — Wire-up

```tsx
// app/providers/PostHogProvider.tsx
'use client';

import { useEffect } from 'react';
import posthog from 'posthog-js';
import { PostHogProvider as Provider } from 'posthog-js/react';
import { installPostHogScriptRewriter } from '@/lib/posthog-rewrite-loader';

if (typeof window !== 'undefined') installPostHogScriptRewriter(); // BEFORE posthog.init

export function PostHogProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
      api_host: 'https://api.agentruntime.app', // unchanged
      capture_dead_clicks: true,
      // session_recording: { ... }
    });
  }, []);
  return <Provider client={posthog}>{children}</Provider>;
}
```

The patcher runs at module load, which is before the `useEffect` that calls `posthog.init`.

---

## Approach B — Full proxy through Next.js

Drop `api.agentruntime.app` from the SDK. Everything goes through your Next.js app, including event capture, decide, session recording uploads, and the static JS chunks.

### B.1 — `next.config.js` rewrites

```js
// next.config.js
const PH_API    = 'https://us.i.posthog.com';        // events, decide, capture, etc.
const PH_ASSETS = 'https://us-assets.i.posthog.com'; // /static/*

module.exports = {
  async rewrites() {
    return [
      // Static chunks — bland aliases for the three blocker-flagged ones
      { source: '/_p/dc.js', destination: `${PH_ASSETS}/static/dead-clicks-autocapture.js` },
      { source: '/_p/r.js',  destination: `${PH_ASSETS}/static/recorder.js` },
      { source: '/_p/r2.js', destination: `${PH_ASSETS}/static/posthog-recorder.js` },

      // All other static chunks (surveys, web-vitals, etc.) — pass-through
      { source: '/_p/static/:path*', destination: `${PH_ASSETS}/static/:path*` },

      // Everything else — events, decide, config, etc.
      { source: '/_p/api/:path*', destination: `${PH_API}/:path*` },
    ];
  },
};
```

### B.2 — Same `installPostHogScriptRewriter` as A.2

The same rewriter still handles the three blocker-flagged filenames. Other static chunks ride on the `/_p/static/:path*` rewrite without any patching.

### B.3 — Wire-up — point `api_host` at your Next.js app

```tsx
posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  api_host: 'https://your-app.example.com/_p/api', // <-- changed
  // assets host is implicit (same as api_host); the rewrites resolve it
  capture_dead_clicks: true,
});
```

You'll also want the rewriter to strip the host on `/static/*` requests so the SDK's lazy-loaded chunks land on `/_p/static/<file>` (same-origin), not `https://your-app.example.com/_p/api/static/<file>`. Either configure `assets_host` on the SDK if your version supports it, or extend the rewriter to also catch `/static/:path*` → `/_p/static/:path*`.

---

## Pros and cons

### Approach A — Surgical (recommended)

**Pros**
- Minimal change, minimal blast radius. Hot path (events, recordings) keeps using PostHog's purpose-built proxy.
- PostHog manages `api.agentruntime.app` — failover, caching, region routing, performance tuning are someone else's problem.
- If your Next.js app slows down or goes offline, PostHog still receives events. Most analytics keep working.
- Cheap. Three small files cached for 4 hours each — negligible bandwidth and zero impact on Next.js function counts.
- Easy to reason about: one rewrite stanza, one client patcher, three filenames.

**Cons**
- Two "proxies" to keep mentally aligned. If PostHog renames a chunk in an SDK upgrade, you'll need to add a new entry. Watch DevTools Network for any `/static/*.js` request leaking through.
- Doesn't help if PostHog adds *new* blocker-flagged filenames in the future. You'll add them as they appear.

### Approach B — Full proxy through Next.js

**Pros**
- Single origin. Simpler from the browser's perspective; no third-party domain in network requests at all.
- Total control: you can add auth, sampling, redaction, custom headers, rate limiting on any PostHog request.
- Uniform renaming. You can rename event capture endpoints too (e.g. `/_p/api/e/` → bland alias) if a blocker ever starts targeting them.
- One less external dependency in the request path — useful if you have strict CSP, want to drop `api.agentruntime.app` from `connect-src`, or are consolidating vendor surfaces.

**Cons**
- **Your Next.js sits in the hot path of every event, every recording chunk, every flag check.** Session recording in particular sends kilobytes per second per active user. On serverless (Vercel functions), that's many invocations per session.
- **Latency.** PostHog's edge is highly optimized. Routing through your Next.js — especially with cold starts on serverless — will be slower. Users on slow networks feel it.
- **Cost.** On Vercel/Cloudflare-style billing, you can 10–100× your function invocation count once recording traffic flows through. Bandwidth out also goes up.
- **Single point of failure.** If your Next.js goes down, all PostHog stops — including basic event capture. With approach A, only the recorder/dead-clicks lazy-load fails for blocked users; everything else still works.
- **Body-size and timeout limits.** Some serverless platforms cap request bodies (e.g. Vercel functions: 4.5MB) and execution time. Session recording payloads can occasionally bump up against these.
- **You're rebuilding what `api.agentruntime.app` already does**, with worse infra for the job.

### Quick comparison

| | A — Surgical | B — Full proxy |
|---|---|---|
| Files routed via Next.js | 3 (cached 4h) | All PostHog traffic |
| Next.js function invocations | Trivial | High (per event, per recording chunk) |
| Failure mode if Next.js is down | Recorder/dead-clicks fail to load for blocked users; rest still works | Total PostHog outage |
| Latency on hot path | Unchanged | Worse (extra hop, possible cold start) |
| Hosting cost impact | Negligible | Potentially significant at scale |
| Setup complexity | Low | Low–medium |
| Future blocker rules | Add a rewrite per filename | Already covered for `/static/*`; rename event paths too if needed |

**My recommendation:** Approach A. The blocker problem is filename-shaped, not transport-shaped — solving it surgically beats adopting a heavier architecture. Revisit B only if (a) you have a hard CSP/compliance requirement to drop `api.agentruntime.app`, or (b) you actually need server-side custom logic on the event stream.

---

## Verify (either approach)

```bash
# Server side
curl -I "https://your-app.example.com/_p/dc.js?v=1.372.10"
curl -I "https://your-app.example.com/_p/r2.js?v=1.372.10"
# Both: 200, content-type: text/javascript
```

Browser, with ad blocker enabled:
- DevTools → Network: requests to `/_p/dc.js` and `/_p/r2.js` succeed.
- No `/static/dead-clicks-autocapture.js` or `/static/posthog-recorder.js` requests visible.
- `posthog.sessionRecordingStarted()` returns `true` after a few seconds.
- Dead-click events appear in PostHog Live Events.

In uBlock Origin's Logger, the `/_p/*` entries should show `--` (allowed), not red.

---

## Notes / gotchas

- **SDK upgrades.** If PostHog renames a chunk, the rewriter silently misses it and the file goes back to being blocked. Pin `posthog-js`. After upgrades, watch DevTools Network for any leaked `/static/*.js` request.
- **Caching.** Rewrites preserve upstream `Cache-Control` (`max-age=14400`) and the `?v=1.372.10` cache-buster. Same caching as PostHog's CDN.
- **Same-origin.** The rewriter strips the host so the request becomes same-origin (`/_p/dc.js`). Avoids CORS preflight on top of blocker bypass.
- **Network-level blockers.** Pi-hole/NextDNS that block by domain won't be bypassed by this. They're a much smaller cohort than browser extensions, and your own domain isn't on those lists.
- **Region.** This doc assumes US cloud (`us-assets.i.posthog.com`, `us.i.posthog.com`). EU users swap to `eu-assets.i.posthog.com` / `eu.i.posthog.com`.

---

## Files to add or change

### Approach A
| File | Change |
|---|---|
| `next.config.js` | Add three rewrites under `/_p/` |
| `lib/posthog-rewrite-loader.ts` | New file — script-tag patcher |
| Your PostHog provider | Call `installPostHogScriptRewriter()` before `posthog.init` |

### Approach B
| File | Change |
|---|---|
| `next.config.js` | Add the three aliases + `/_p/static/:path*` + `/_p/api/:path*` rewrites |
| `lib/posthog-rewrite-loader.ts` | Same patcher (still needed for the three blocker-flagged filenames) |
| Your PostHog provider | Same patcher call **and** `api_host: 'https://your-app.example.com/_p/api'` |
