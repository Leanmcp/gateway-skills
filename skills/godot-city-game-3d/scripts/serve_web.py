#!/usr/bin/env python3
"""Serve a Godot web export locally, with the two headers it cannot boot without.

    python3 serve_web.py --dir build/web --port 8000

Godot's web build uses threads, which means SharedArrayBuffer, which browsers
only expose to *cross-origin isolated* pages. Isolation is requested with:

    Cross-Origin-Opener-Policy:   same-origin
    Cross-Origin-Embedder-Policy: require-corp

`python3 -m http.server` sends neither, so the files download fine and then the
game silently fails to start -- usually with nothing but a console warning about
SharedArrayBuffer. Those two headers are the entire difference, which is why
this file exists instead of a one-liner.

The same requirement applies to whatever you deploy to. On static hosts:
  * Netlify / Cloudflare Pages -- a _headers file
  * Vercel                     -- headers[] in vercel.json
  * GitHub Pages               -- cannot set headers; export without thread
                                  support, or host elsewhere
"""

import argparse
import functools
import http.server
import os
import socketserver


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".wasm": "application/wasm",
        ".js": "text/javascript",
        ".pck": "application/octet-stream",
    }

    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        # A stale wasm/pck served from cache after a re-export is a confusing
        # class of bug: the page loads and behaves like the previous build.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        if "404" in (fmt % args):
            super().log_message(fmt, *args)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--dir", default=".")
    ap.add_argument("--bind", default="", help="0.0.0.0 to expose on the LAN")
    args = ap.parse_args()

    os.chdir(args.dir)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer((args.bind, args.port), Handler) as httpd:
        print(f"serving {os.getcwd()} on http://localhost:{args.port}")
        print("COOP/COEP headers are set -- SharedArrayBuffer will be available")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
