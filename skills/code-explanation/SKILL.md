---
name: code-explanation
description: >-
  Generate a complete, beginner-friendly explanation of an entire code
  repository as a set of markdown files. Maps the repo structure with `treecap`
  (installing it if missing), studies the actual source, then writes a
  `CODE_EXPLANATION/` folder containing an `OVERVIEW.md` plus numbered deep-dive
  files (01_architecture.md, 02_models.md, ...) that explain how the code is
  built, what it does, and how the pieces fit together — illustrated with real
  code excerpts. Use this skill whenever the user wants to understand,
  document, onboard onto, or get a walkthrough of a codebase: phrases like
  "explain this repo", "explain the code", "code explanation", "walk me through
  this codebase", "help me understand how this is built", "document the
  architecture", or "what does this project do" — even if they don't say the
  word "skill". Prefer this over ad-hoc summaries whenever the goal is a
  durable, written explanation of a whole repo.
---

# Code Explanation

Produce a thorough written explanation of an entire repository so someone new
can understand **what it does, how it is built, and how the pieces fit
together**. The output is a `CODE_EXPLANATION/` folder of markdown files: one
`OVERVIEW.md` and a series of numbered deep-dive documents.

The goal is genuine understanding, not a file inventory. A good explanation
reads like a knowledgeable engineer walking a new teammate through the codebase:
it names the important abstractions, shows real code, and explains *why* things
are shaped the way they are.

## Workflow

### 1. Establish the structural map with `treecap`

Before reading any code, get a bird's-eye view of the repo layout. Use
`treecap`, a tree viewer that caps how many entries it shows per folder so large
repos stay readable.

Resolve the tool in this order:

1. **`treecap`** — preferred. Check with `which treecap`.
2. If it is missing, **install it**: `pip install treecap` (it is a PyPI
   package: https://pypi.org/project/treecap/). If `pip` isn't available, try
   `pip3 install treecap` or `python -m pip install treecap`.
3. If installation fails or is declined, **fall back to `tree`**
   (`which tree`).
4. If neither exists, fall back to a manual listing (e.g. `find . -type f`
   filtered sensibly), but prefer the real tools.

Run it on the target repo. Sensible defaults:

```bash
treecap -W 0 -L 3        # full width (all entries), 3 levels deep
```

`-W` caps entries shown per directory (`0` = unlimited; the default is 5).
`-L` caps display depth. Start broad, then re-run deeper or with a higher width
on the directories that turn out to matter (e.g. `treecap src -W 0`). `treecap`
skips `.git`, `node_modules`, `__pycache__`, and `.venv` by default, which is
usually what you want.

Capture this tree — you'll embed a trimmed version of it in `OVERVIEW.md`.

### 2. Read the code and build a mental model

Now actually understand the repo. Don't write any explanation files until you
have a real model of how it works. Investigate in roughly this order, because
each step gives you vocabulary for the next:

- **Entry points & manifests** — `package.json`, `pyproject.toml`,
  `Cargo.toml`, `go.mod`, `main.*`, `index.*`, `app.*`, CLI definitions,
  server bootstraps. These tell you what the project *is* (library? service?
  CLI? web app?), its tech stack, and how it starts.
- **Core data shapes** — Pydantic models, dataclasses, TypeScript
  types/interfaces, ORM/DB schemas, protobufs, GraphQL schemas. These are the
  nouns of the system and the fastest way to understand the domain. They almost
  always deserve an early deep-dive file.
- **Architecture & control flow** — how requests/commands flow through the
  system, the major layers/modules and their dependencies, key design patterns.
- **Major subsystems** — each significant module, package, or feature area,
  one at a time.
- **Cross-cutting concerns** — config, auth, error handling, logging,
  persistence, external integrations.

Read the real source. Quote it later. If the repo is large, prioritize the
code that carries the most meaning over exhaustively covering every file.

### 3. Create the `CODE_EXPLANATION/` folder and write the docs

Create a `CODE_EXPLANATION/` directory at the root of the repo being explained.
Inside it, write `OVERVIEW.md` first, then numbered deep-dive files.

#### OVERVIEW.md

This is the front door. Include:

- **What this project is** — one or two paragraphs: purpose, what problem it
  solves, what kind of thing it is (service/library/CLI/app).
- **Tech stack** — languages, frameworks, key libraries, datastores.
- **High-level architecture** — a short narrative of how the major pieces fit,
  plus the trimmed `treecap` tree annotated with what each top-level
  directory/file is for.
- **Reading guide** — a table of contents listing every numbered file with a
  one-line description, so the reader knows where to go.

#### Numbered deep-dive files (`01_*.md`, `02_*.md`, …)

Order them **foundational-first**, so each file builds on the previous. A
typical-but-not-mandatory ordering:

- `01_architecture.md` — the big picture: layers, modules, data/control flow,
  how a typical operation travels through the system end to end.
- `02_models.md` (or `02_types.md` / `02_data_model.md`) — the core data
  structures (Pydantic models, TS types, schemas). These are foundational
  vocabulary, so explain them early.
- `03_*.md` onward — each major subsystem/module/feature, one per file.
- Later files — cross-cutting concerns (config, auth, errors), key end-to-end
  flows, and how to run/extend the project.

Adapt the exact split and naming to the repo. A small CLI might need 3 files; a
large service might need 10. Use descriptive slugs (`04_auth_and_sessions.md`,
not `04_misc.md`).

## How to write the explanations

**Explain code with real code.** This is the core of the skill. For each
important abstraction, show an actual excerpt from the repo (with a
`path/to/file.py:line`-style reference), then explain what it does and why it
matters. Prefer real snippets over invented pseudo-code. Trim long blocks to the
revealing parts with `# ...` rather than pasting hundreds of lines.

````markdown
The central request handler lives in `src/server/handler.py`:

```python
class RequestHandler:
    def __init__(self, store: Store, auth: AuthService):
        self.store = store
        self.auth = auth

    async def handle(self, req: Request) -> Response:
        user = await self.auth.verify(req.token)   # 1. authenticate
        record = await self.store.fetch(req.id)    # 2. load state
        return self._render(record, user)          # 3. shape response
```

Every inbound request flows through `handle()`: it authenticates the caller,
loads the relevant record, and renders a response. Note the dependency
injection in `__init__` — `Store` and `AuthService` are passed in rather than
constructed here, which is what makes the handler unit-testable.
````

**Explain the why, not just the what.** Point out design decisions, trade-offs,
patterns, and non-obvious connections between files. "This uses a registry
pattern so plugins can self-register at import time" is far more useful than
"this is a dictionary."

**Do not explain documentation or markdown.** Existing docs, READMEs, changelogs,
license files, and other prose are *not* the target — the code is. Don't
summarize their contents. If they're worth pointing to, just list them briefly
(e.g. a short "Existing documentation" section noting "`docs/api.md` — API
reference; `CONTRIBUTING.md` — contributor guide") so the reader knows they
exist, and move on.

**Write for a capable newcomer.** Assume the reader is a competent engineer who
has never seen *this* repo. Define project-specific jargon. Use diagrams in
fenced code blocks (ASCII or mermaid) when a flow or hierarchy is easier shown
than told.

**Be accurate.** Only describe code you've actually read. If something is
unclear or you're inferring, say so rather than inventing behavior.

## Quick checklist

- [ ] Resolved a tree tool (`treecap` preferred, installed if missing, else `tree`)
- [ ] Captured the repo structure
- [ ] Read entry points, core models/types, and major modules before writing
- [ ] Created `CODE_EXPLANATION/` at the repo root
- [ ] `OVERVIEW.md` with purpose, stack, architecture, annotated tree, and a TOC
- [ ] Numbered files, foundational-first (architecture/models early)
- [ ] Real code excerpts with file references throughout
- [ ] Explained the *why*, not just the *what*
- [ ] Docs/markdown listed, not explained
