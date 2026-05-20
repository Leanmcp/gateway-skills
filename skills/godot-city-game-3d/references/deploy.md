# Deploy — getting the game in front of other people

Contents: [Pick a path](#pick-a-path) · [Web export](#web-export) ·
[Hosting the web build](#hosting-the-web-build) · [Cloud GPU streaming](#cloud-gpu-streaming) ·
[Which GPU](#which-gpu) · [What it costs](#what-it-costs) ·
[How many players per GPU](#how-many-players-per-gpu) · [Desktop builds](#desktop-builds)

## Pick a path

Godot has **no built-in pixel streaming**. Unreal ships Pixel Streaming; Godot's
WebRTC support is for *multiplayer networking*, not video — a common and
expensive confusion. There are exactly two real paths.

| | Web export | Cloud GPU streaming |
|---|---|---|
| Cost | ~$0 | ~$0.35–0.60 per player-hour, all-in |
| Latency | zero, runs locally | 30–60 ms you cannot engineer away |
| Concurrent players | unlimited | 1–4 per GPU |
| Renderer | Compatibility (WebGL 2) only | full Forward+ |
| Ops | none | real |

**Default to web export.** Reach for cloud streaming only when players *cannot*
run the game — Chromebooks, phones, locked-down work laptops — or for an instant
no-download demo link.

If the motivation is "my laptop runs hot", neither is the answer. Cap the
framerate first: `run/max_fps=60` plus vsync typically halves GPU power draw at
zero latency cost, and cloud streaming solves a hot laptop the way moving house
solves a leaky tap. After the cap, in order of effect: shadow distance,
`visibility_range_end` on the building multimeshes, Forward+ → Mobile,
`scaling_3d_scale` at 0.75.

## Web export

```bash
bash scripts/export_web.sh          # export + serve with the right headers
bash scripts/export_web.sh --no-serve
```

Three things must all be true, and each fails differently:

1. **Export templates installed** — `bash install_godot.sh --templates`. The
   most common failure on a fresh machine, and the error message blames the
   preset.
2. **A preset named exactly `Web`** — `ensure_export_presets.py` writes one. It
   is normally only creatable through the editor GUI, which does not exist on a
   VM.
3. **Compatibility renderer.** Browsers run WebGL 2 only; Forward+ and WebGPU do
   not run there. Override just the web platform so the desktop build keeps its
   renderer:

   ```ini
   [rendering]
   renderer/rendering_method="forward_plus"
   renderer/rendering_method.web="gl_compatibility"
   ```

Be honest about the visual cost: a city authored for Forward+ (SSAO, SSIL, glow,
volumetric fog) looks flatter under Compatibility. Several of those effects drop
or degrade. Budget a day of art tuning, not five minutes.

## Hosting the web build

Godot's web build uses threads, which means `SharedArrayBuffer`, which browsers
only expose to **cross-origin isolated** pages. That requires two headers:

```
Cross-Origin-Opener-Policy:   same-origin
Cross-Origin-Embedder-Policy: require-corp
```

`python3 -m http.server` sends neither, the files download fine, and the game
silently fails to boot with nothing but a console warning. Those two headers are
the entire difference — which is why `serve_web.py` exists instead of a
one-liner.

| Host | How |
|---|---|
| Netlify, Cloudflare Pages | a `_headers` file |
| Vercel | `headers[]` in `vercel.json` |
| S3 + CloudFront | response-headers policy |
| GitHub Pages | **cannot set headers** — export without thread support, or host elsewhere |

Also serve `.wasm` as `application/wasm` and send `Cache-Control: no-store`
during development; a cached `.wasm` or `.pck` after a re-export produces a page
that loads and behaves like the previous build.

## Cloud GPU streaming

Render on a cloud GPU, encode to H.264 with the GPU's NVENC chip, ship video to
a browser over WebRTC, send input back. The mature open-source stack is
[Selkies](https://github.com/selkies-project/selkies) — started by Google
engineers; effectively self-hosted Stadia.

```bash
bash scripts/cloud/provision_gcp.sh     # create the VM (5-10 min of setup)
bash scripts/cloud/deploy_game.sh       # export Linux build, push, start
bash scripts/cloud/stop.sh              # STOP BILLING
open http://<ip>:8080
```

Four things eat time, in the order you will meet them:

1. **GPU quota.** A new GCP project has a global GPU quota of **zero**. Request
   an increase (IAM & Admin → Quotas → `NVIDIA_L4_GPUS`) — approval takes hours
   to days, and everything else is blocked on it. `provision_gcp.sh` preflights
   this so you find out in seconds rather than after a ten-minute setup.
2. **Headless X.** Datacenter GPUs have no display output, so there is no X
   server for Godot to open and it exits instantly with "cannot open display".
   The streaming container runs its own X server bound to the GPU. This is the
   classic failure point.
3. **Multi-session.** One player works out of the box. Several concurrent
   players means one container, X display and port per session plus a router in
   front — a real backend project, not a config change.
4. **Latency tuning.** Region choice dominates. 100 ms of geography ruins a
   first-person game no matter how good the encoder is. Pick the zone nearest
   your players.

Change the default Selkies basic-auth password before showing anyone the link.

Timeline: **an afternoon** for one player streaming to your browser. **A week or
more** for something several people use reliably.

## Which GPU

| GPU | Machine | GPU $/hr | ~Total $/hr | Notes |
|---|---|---|---|---|
| **L4** | `g2-standard-8` | ~$0.71 | **~$0.90** | 24 GB, 2 NVENC engines, AV1. Best price/perf. |
| **T4** | `n1-standard-8` + T4 | ~$0.35 | **~$0.73** | 16 GB, 1 NVENC. Cheapest that still hardware-encodes. |
| A100 / H100 | — | $3–10 | — | Built for training, not graphics. Wrong tool. |

L4 comes only on G2 machine types, where the GPU is part of the machine. T4
attaches to N1 as a separate accelerator. They are not interchangeable, and
mixing them up produces an unhelpful "invalid machine type".

**Recommendation: L4 spot.** Spot is 60–70% off and GCP can reclaim it with 30
seconds' notice — fine for a dev box you are watching, not fine for players you
promised uptime to.

Prices are on-demand `us-central1` and move; verify before committing.

## What it costs

| Usage | L4 on-demand | L4 spot |
|---|---|---|
| 2 hrs/day | ~$54/mo | ~$18/mo |
| 8 hrs/day | ~$216/mo | ~$72/mo |
| 24/7 | ~$650/mo | ~$220/mo |

Plus ~$10/mo per 100 GB boot disk **even while the VM is stopped**, and egress
at ~$0.08–0.12/GB. Video streaming is bandwidth-heavy: 12 Mbit/s is ~5.4 GB per
hour, so a single player costs roughly $0.50/hour in egress alone. At any scale
that can exceed the GPU cost.

`stop.sh` stops compute billing; `DELETE=1 stop.sh` removes the disk too. Use it
religiously — a forgotten VM is the most common way this gets expensive.

## How many players per GPU

This is where estimates usually go wrong, so be careful which limit binds.

**Encoding is not the bottleneck.** NVIDIA does not restrict concurrent NVENC
sessions on datacenter GPUs (unlike GeForce cards, capped at 3–5); a T4 is
documented handling up to 24 parallel 1080p30 encode streams.

**Rendering is the bottleneck.** Every player needs their own full render of a
city with thousands of buildings, shadows and post-processing.

| GPU | Comfortable at 1080p60 | Pushing it |
|---|---|---|
| T4 | 1–2 players | 3 |
| L4 | 3–4 players | 6 |

Halve at 1440p, roughly double at 720p30. Each player also needs their own Godot
process, X display and ~2–3 GB of VRAM, so an L4's 24 GB caps you around 6–8
sessions regardless of raw speed.

## Desktop builds

```bash
python3 scripts/ensure_export_presets.py --preset macOS --preset "Windows Desktop"
godot --headless --path game --export-release "macOS" build/game.dmg
```

Notes: macOS builds need codesigning and notarization to run on anyone else's
machine without a Gatekeeper warning (the preset writes `codesign/enable=false`,
which is right for local testing and wrong for distribution). Linux builds
should embed the `.pck` (`binary_format/embed_pck=true`) so deployment is one
file to copy rather than two that must stay together.
