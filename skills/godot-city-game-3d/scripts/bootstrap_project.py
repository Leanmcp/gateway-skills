#!/usr/bin/env python3
"""Scaffold a new Godot 4 procedural-city project that runs immediately.

    python3 bootstrap_project.py ~/code/my-city
    python3 bootstrap_project.py ~/code/my-city --city harbour --name "Harbour Run"
    python3 bootstrap_project.py . --no-workspace     # templates only

What you get is a project that builds a hilly ~60-block city with batched,
window-shaded buildings, collision, a walkable first-person player, and a copy
of the operate scripts (install / run / check / export / cloud) under
`workspace/`. It is deliberately a *working small city* rather than an empty
skeleton -- the value of this scaffold is the architecture it demonstrates
(config as data, one height function, MultiMesh batching, box collision,
nothing generated saved into the scene), and an empty skeleton demonstrates
none of it.

Copying the workspace scripts in, rather than referencing the skill, is what
makes the result portable: the new repo carries everything needed to stand
itself up on another laptop, a CI runner or a cloud VM.
"""

import argparse
import pathlib
import re
import shutil
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATES = HERE / "templates"

# Scripts copied into the new project's workspace/. cloud/ is copied wholesale.
WORKSPACE_FILES = [
    "lib.sh",
    "install_godot.sh",
    "run.sh",
    "check_project.sh",
    "import_assets.sh",
    "build_assets.sh",
    "export_web.sh",
    "serve_web.py",
    "ensure_export_presets.py",
]

README = """# {name}

A procedurally generated 3D city in [Godot 4](https://godotengine.org).

The city is not modelled. `game/scripts/city/city_config_{city}.gd` is a table of
block sizes, district rules and weighted building types; the generator reads it
and builds the whole thing at load time. Changing one number there re-rhythms a
square kilometre.

## Setup

```bash
bash workspace/install_godot.sh --templates
```

`--templates` also installs the export templates, which you need for the web
and cloud builds and cannot install headlessly any other way.

## Play

```bash
bash workspace/run.sh
bash workspace/run.sh --editor       # open the editor instead
```

## Verify it builds, headlessly

```bash
time bash workspace/check_project.sh
```

No window opens, so this works over SSH and in CI. It fails on GDScript and
shader errors, which Godot otherwise reports while still exiting 0.

## Share it

```bash
bash workspace/export_web.sh          # WebAssembly, runs on the player's machine
bash workspace/cloud/provision_gcp.sh # GPU VM streaming to a browser (costs money)
bash workspace/cloud/stop.sh          # stop billing
```

## Controls

| Input | Action |
|---|---|
| Mouse | Look |
| W A S D / arrows | Move |
| Shift | Sprint |
| Space | Jump |
| U | Cycle movement speed (1x / 3x / 8x) |
| Esc | Release the mouse |

## Where to change things

| Want to change | File |
|---|---|
| Block sizes, districts, hills, seed | `game/scripts/city/city_config_{city}.gd` |
| What a building kind looks like | `game/scripts/city/typology.gd` |
| Ground shape | `game/scripts/city/terrain.gd` |
| Batching, collision, placement | `game/scripts/city/city_generator.gd` |
| Windows, storeys, night lighting | `game/shaders/facade.gdshader` |
| Movement feel | `game/scripts/player.gd` |

Add a second city by copying the config file, adding it to `CONFIGS` in
`city_generator.gd`, and running with `CITY=<name>`. The generator needs no
changes -- that is the point of keeping it free of any one city's knowledge.
"""

GITIGNORE = """# Godot's import cache and derived data. Regenerate with:
#   bash workspace/import_assets.sh
game/.godot/
game/android/

# Build output
build/
export_presets.cfg

.DS_Store
"""


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9_]+", "_", text.lower()).strip("_")
    return slug or "city"


def render(text: str, subs: dict) -> str:
    for key, value in subs.items():
        text = text.replace("{{%s}}" % key, value)
    return text


def copy_tree(src: pathlib.Path, dst: pathlib.Path, subs: dict, force: bool) -> list[str]:
    written = []
    for path in sorted(src.rglob("*")):
        if path.is_dir():
            continue
        rel = render(str(path.relative_to(src)), subs)
        target = dst / rel
        if target.exists() and not force:
            print(f"  skip  {rel} (exists; --force to overwrite)")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(path.read_text(), subs))
        written.append(rel)
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="directory for the new project (created if absent)")
    ap.add_argument("--city", default="", help="config slug, e.g. 'harbour' (default: from --name)")
    ap.add_argument("--name", default="", help="project display name (default: from target dir)")
    ap.add_argument("--no-workspace", action="store_true",
                    help="skip copying the run/build/deploy scripts")
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    args = ap.parse_args()

    target = pathlib.Path(args.target).expanduser().resolve()
    name = args.name or target.name.replace("-", " ").replace("_", " ").title()
    city = slugify(args.city or name)

    subs = {"CITY": city, "CITY_TITLE": city.replace("_", " ").title(), "PROJECT_NAME": name}

    if not TEMPLATES.is_dir():
        sys.exit(f"templates missing at {TEMPLATES}")

    game = target / "game"
    game.mkdir(parents=True, exist_ok=True)
    print(f"project: {name}\ncity:    {city}\ntarget:  {target}\n")

    written = copy_tree(TEMPLATES, game, subs, args.force)
    for rel in written:
        print(f"  ++    game/{rel}")

    if not args.no_workspace:
        ws = target / "workspace"
        (ws / "cloud").mkdir(parents=True, exist_ok=True)
        for fname in WORKSPACE_FILES:
            src = HERE / fname
            if not src.exists():
                continue
            dst = ws / fname
            if dst.exists() and not args.force:
                continue
            shutil.copy2(src, dst)
            dst.chmod(dst.stat().st_mode | stat.S_IXUSR)
            print(f"  ++    workspace/{fname}")
        for src in sorted((HERE / "cloud").glob("*")):
            dst = ws / "cloud" / src.name
            if dst.exists() and not args.force:
                continue
            shutil.copy2(src, dst)
            dst.chmod(dst.stat().st_mode | stat.S_IXUSR)
            print(f"  ++    workspace/cloud/{src.name}")

    for fname, body in (("README.md", README.format(name=name, city=city)),
                        (".gitignore", GITIGNORE)):
        path = target / fname
        if not path.exists() or args.force:
            path.write_text(body)
            print(f"  ++    {fname}")

    print(f"""
Done. Next, on this machine:

  bash {target}/workspace/install_godot.sh --templates
  time bash {target}/workspace/check_project.sh     # headless, proves it builds
  bash {target}/workspace/run.sh                    # play it

The check is worth running first -- it exercises the generator end to end
without opening a window, so a mistake shows up as a message rather than as a
black screen.
""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
