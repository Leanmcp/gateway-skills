# Setup — getting a Godot city project running anywhere

Contents: [Install](#install) · [Where things live](#where-things-live) ·
[Headless everything](#headless-everything) · [A second machine](#a-second-machine) ·
[CI](#ci) · [Version pinning](#version-pinning)

## Install

```bash
bash scripts/install_godot.sh --templates
```

Godot 4 is a single binary with no runtime dependency, which is what makes this
easy: there is no toolchain, no SDK, no account, and no per-machine
configuration. The installer handles macOS (brew cask or direct download) and
Linux (direct download to `~/.local/bin/godot`), clears the macOS quarantine
flag, and puts `godot` on `PATH`.

**Always pass `--templates` on any machine that will export.** Export templates
are a separate ~1 GB download that Godot normally fetches through an editor
dialog. Without them `--export-release` fails with a message that reads like a
preset problem, and on a headless VM the documented fix (open the editor) does
not exist. Installing them from the same script is what makes web and cloud
export scriptable.

Verify:

```bash
godot --version                              # expect 4.x
bash scripts/check_project.sh                # headless build of the project
```

## Where things live

| | macOS | Linux |
|---|---|---|
| Engine | `/Applications/Godot.app/Contents/MacOS/Godot` | `~/.local/bin/godot` |
| Editor + export config | `~/Library/Application Support/Godot/` | `~/.local/share/godot/` |
| Export templates | `…/Godot/export_templates/<ver>.stable/` | `…/godot/export_templates/<ver>.stable/` |

Inside the repo:

| Path | Committed? | Why |
|---|---|---|
| `game/project.godot` | yes | project settings, autoloads, physics layers |
| `game/.godot/` | **no** | import cache; rebuild with `import_assets.sh` |
| `game/*.import` | yes | import *settings* for each asset — losing these changes how assets load |
| `export_presets.cfg` | usually no | machine-specific paths; regenerate with `ensure_export_presets.py` |
| `build/` | no | output |

The `.godot/` distinction trips people up: `.import` files are source (they
record how you configured an asset), `.godot/imported/` is derived (the
converted binaries). Commit the first, ignore the second.

## Headless everything

Every operation has a no-window form, which is what makes this work over SSH,
in CI, and on a cloud VM:

```bash
godot --headless --path game --import                      # reimport assets
godot --headless --path game --quit-after 600 res://scenes/main.tscn
godot --headless --path game --export-release "Web" out/index.html
godot --headless --path game --script res://tools/bake.gd  # run a script, no scene
```

`--quit-after N` counts **frames**, not seconds. At 60 fps, 600 frames ≈ 10 s —
enough for a city generator to finish and report.

The critical gotcha: **Godot exits 0 even when GDScript throws at runtime.** A
green exit code proves nothing. `check_project.sh` exists because of this — it
scrapes the log for `SCRIPT ERROR`, `Parse Error` and friends and fails on them.
Any CI gate you build must do the same or it will pass a broken build.

## A second machine

The whole point of keeping the scripts in the repo is that a new machine is:

```bash
git clone <repo> && cd <repo>
bash workspace/install_godot.sh --templates
bash workspace/check_project.sh
bash workspace/run.sh
```

Nothing is machine-specific except the Godot binary location, and `lib.sh`
resolves that by searching rather than hardcoding. Override anything with
environment variables instead of editing files:

```bash
export GODOT_BIN=/opt/godot/godot      # non-standard install
export GODOT_PROJECT=/repo/game        # non-standard layout
export GODOT_VERSION=4.7.1             # what install_godot.sh fetches
```

## CI

```yaml
- run: bash workspace/install_godot.sh --templates
- run: bash workspace/check_project.sh
```

Cache `~/.local/bin/godot` and the export-templates directory between runs; the
engine download is the slow part, and it never changes unless you bump the pin.
Do **not** cache `game/.godot/` — a stale import cache produces failures that
look like source bugs.

## Version pinning

Pin the engine version in one place and let everything read it. `lib.sh` uses
`GODOT_VERSION` (default 4.7.1) and the cloud host reads the same value through
instance metadata, so the VM cannot drift from the laptop.

Two rules worth keeping:

- **Export templates must match the engine build exactly.** 4.7.1 templates and
  a 4.7.0 engine fail at export. The installer reads the version back from the
  binary rather than trusting the variable, for exactly this reason.
- **Godot 4 minor releases do move GDScript and rendering behaviour.** Bump
  deliberately, and re-run `check_project.sh` on both cities before committing
  the bump.
