#!/usr/bin/env python3
"""Make `--export-release` work from a shell, by writing the export presets
Godot would otherwise expect you to click through the editor GUI to create.

    python3 ensure_export_presets.py                  # Web + Linux
    python3 ensure_export_presets.py --preset Web
    python3 ensure_export_presets.py --project path/to/project --preset macOS

Why this exists: `godot --export-release "Web" out/index.html` fails unless a
preset *named exactly* "Web" already exists in export_presets.cfg, and that file
is normally only ever written by the editor. On a headless VM or a fresh clone
there is no editor to open, so the documented fix is unavailable and the error
message ("Unknown export preset") does not say that a file is missing.

Presets here are deliberately minimal. Godot fills in every option it does not
find with its default, so listing fewer keys is more robust across engine
versions than pasting a full preset from one version into another.

Existing presets are never modified -- if a preset with the requested name is
already there, it is left exactly as the user configured it.
"""

import argparse
import pathlib
import re
import sys

# Only the options that must not be left at their default, per platform.
PRESETS = {
    "Web": {
        "platform": "Web",
        "options": {
            # Godot's web build needs SharedArrayBuffer, which needs threads.
            "variant/thread_support": "true",
            "vram_texture_compression/for_desktop": "true",
            "vram_texture_compression/for_mobile": "true",
        },
    },
    "Linux": {
        "platform": "Linux",
        "options": {
            "binary_format/architecture": '"x86_64"',
            # One self-contained file is far easier to scp to a VM than a
            # binary plus a .pck that must stay beside it.
            "binary_format/embed_pck": "true",
            "texture_format/s3tc_bptc": "true",
        },
    },
    "macOS": {
        "platform": "macOS",
        "options": {
            "binary_format/architecture": '"universal"',
            "codesign/enable": "false",
            "notarization/notarization": "0",
        },
    },
    "Windows Desktop": {
        "platform": "Windows Desktop",
        "options": {
            "binary_format/architecture": '"x86_64"',
            "binary_format/embed_pck": "true",
        },
    },
}


def find_project(start: pathlib.Path) -> pathlib.Path:
    d = start.resolve()
    for candidate in [d, *d.parents]:
        if (candidate / "project.godot").is_file():
            return candidate
        for sub in ("game", "godot", "client"):
            if (candidate / sub / "project.godot").is_file():
                return candidate / sub
    sys.exit(f"no project.godot found at or above {start}")


def existing_names(text: str) -> set[str]:
    return set(re.findall(r'^name="([^"]*)"', text, re.MULTILINE))


def next_index(text: str) -> int:
    used = [int(n) for n in re.findall(r"^\[preset\.(\d+)\]", text, re.MULTILINE)]
    return max(used) + 1 if used else 0


def render(index: int, name: str, spec: dict) -> str:
    opts = "\n".join(f"{k}={v}" for k, v in spec["options"].items())
    return f"""
[preset.{index}]

name="{name}"
platform="{spec['platform']}"
runnable=true
advanced_options=false
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path=""
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false
script_export_mode=2

[preset.{index}.options]

custom_template/debug=""
custom_template/release=""
{opts}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", default=".", help="project dir, or anywhere inside the repo")
    ap.add_argument(
        "--preset",
        action="append",
        choices=sorted(PRESETS),
        help="repeatable; defaults to Web and Linux",
    )
    args = ap.parse_args()

    project = find_project(pathlib.Path(args.project))
    wanted = args.preset or ["Web", "Linux"]

    cfg = project / "export_presets.cfg"
    text = cfg.read_text() if cfg.exists() else ""
    have = existing_names(text)

    added = []
    for name in wanted:
        if name in have:
            print(f"  ok   preset {name!r} already present, left untouched")
            continue
        text = text.rstrip() + "\n" + render(next_index(text), name, PRESETS[name])
        added.append(name)

    if added:
        cfg.write_text(text.lstrip() + "\n")
        print(f"  ++   added {', '.join(added)} to {cfg}")
    print(f"\nProject: {project}")
    print("Export templates must also be installed:")
    print("  bash install_godot.sh --templates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
