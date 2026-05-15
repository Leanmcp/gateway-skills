---
name: translate-explanation
description: >-
  Translate existing code-explanation docs into another language, Chinese by
  default. Translates a whole `CODE_EXPLANATION/` folder into a parallel
  `CODE_EXPLANATION_<LANG>` copy (e.g. `CODE_EXPLANATION_ZH`), or a single file —
  either bilingually in place (English + translation interleaved) for small files
  or as a `<name>_<lang>.<ext>` sidecar copy for larger ones. Keeps filenames,
  code, identifiers, file paths, and technical terms in English — only the
  explanatory prose is translated. Use this
  skill whenever the user wants to translate, localize, or produce a
  non-English version of code-explanation / codebase documentation: phrases like
  "translate-explanation", "translate the code explanation", "translate the
  CODE_EXPLANATION folder", "localize these docs to Chinese", "make a Chinese
  version of the explanation", or naming any target language for the explanation
  files. Default to Chinese (ZH) when no language is specified.
---

# Translate Explanation

Translate generated code-explanation docs (the kind produced by the
`code-explanation` skill) into another language. The prose is translated but
everything technical stays in English so the docs remain accurate and usable by
engineers.

**Default language is Chinese (`ZH`).** If the user names another language, use
its code instead (see the table below).

## Translation modes

First decide what's being translated — a whole folder or a single file — because
the output shape differs.

**Folder mode (default).** The target is a `CODE_EXPLANATION/` folder (or any
folder of docs). Produce a parallel folder named `<FOLDER>_<LANG>` (e.g.
`CODE_EXPLANATION_ZH`) with the same files. See *Folder mode* below.

**Single-file mode.** The target is one file. Choose between two output styles
based on the file's length, because what's pleasant to read differs by size:

- **Bilingual / interleaved (small files, < 50 lines).** Update the file
  in place so each prose line is immediately followed by its translation —
  English line, then Chinese line. For short files this keeps original and
  translation together and is easy to scan. See *Single-file mode → Bilingual*.
- **Sidecar file (larger files, ≥ 50 lines).** Don't clutter a long file with
  interleaving. Instead create a fully-translated copy named
  `<name>_<lang>.<ext>` (e.g. `notes_zh.md`) in the **same folder**, leaving the
  original untouched. See *Single-file mode → Sidecar*.

Use the line count of the source file to pick the style; if the user explicitly
asks for one style, honor that regardless of size.

In every mode, the rules in *What to translate vs. keep as-is* apply.

## Folder mode

### 1. Locate the source folder

Find the explanation folder to translate. By default this is `CODE_EXPLANATION/`
at the repo root. If it isn't there, search for it
(`find . -type d -name 'CODE_EXPLANATION' -not -path '*/node_modules/*'`) and
confirm with the user if there are multiple candidates. List its files so you
know exactly what to translate — typically `OVERVIEW.md` and numbered files like
`01_architecture.md`, `02_models.md`, etc.

### 2. Resolve the target language and output folder

Map the requested language to a short uppercase code and create the output
folder `CODE_EXPLANATION_<CODE>` as a sibling of the source folder.

| Language  | Code | Output folder              |
|-----------|------|----------------------------|
| Chinese   | `ZH` | `CODE_EXPLANATION_ZH`       |
| Spanish   | `ES` | `CODE_EXPLANATION_ES`       |
| French    | `FR` | `CODE_EXPLANATION_FR`       |
| German    | `DE` | `CODE_EXPLANATION_DE`       |
| Japanese  | `JA` | `CODE_EXPLANATION_JA`       |
| Korean    | `KO` | `CODE_EXPLANATION_KO`       |
| Hindi     | `HI` | `CODE_EXPLANATION_HI`       |
| Portuguese| `PT` | `CODE_EXPLANATION_PT`       |

If no language is given, **default to Chinese (`ZH`)**. For a language not in the
table, use its common two-letter ISO 639-1 code, uppercased.

### 3. Translate each file, one by one

For every file in the source folder, create a file with the **exact same name**
in the output folder. Filenames never change — `01_architecture.md` stays
`01_architecture.md`, not `01_架构.md`. This keeps the two folders aligned
side by side so a reader can compare them file-for-file.

Translate the **prose** into the target language while keeping everything
technical in English. Read each source file, translate its content, and write
the result. Don't translate by guesswork from filenames — translate the actual
content.

## Single-file mode

When the target is a single file (not a folder), first count its lines to choose
the output style, then resolve the language code (Chinese/`ZH` by default).

### Bilingual / interleaved (small files, < 50 lines)

Edit the file **in place**. After each translatable prose line, insert its
translation on the next line, so the file alternates English then the target
language. This keeps a short file readable as a single bilingual document.

- Leave **code blocks verbatim and unduplicated** — never interleave inside a
  fenced block; just keep it once.
- For a heading, put the original heading, then the translated heading on the
  next line (both as headings).
- Blank lines and structure stay intact.

Example (English file → bilingual):

```markdown
# Architecture
# 架构

The handler authenticates the caller, then renders a response.
该 handler 会对调用方进行认证，然后渲染出一个 response。
```

### Sidecar file (larger files, ≥ 50 lines)

Don't interleave a long file — it becomes hard to read. Instead create a new
file in the **same folder** named `<name>_<lang>.<ext>`: take the original
filename, insert `_<lang>` before the extension (lowercase code), e.g.
`design.md` → `design_zh.md`, `README.txt` → `README_zh.txt`. Write a complete
translation there following the standard rules, and leave the original file
unchanged.

## What to translate vs. keep as-is

The guiding idea: an engineer reading the translated docs should see their own
language for the *explanations*, but the exact same code and terminology they'd
find in the editor. Translating an identifier or a library name would make the
docs wrong and unsearchable, so leave those untouched.

**Translate** (the prose):
- Sentences and paragraphs that explain things.
- The descriptive part of headings — but keep technical nouns in English.
  Example: `## Data models and validation` → `## 数据模型与 validation`
  (translate the connective prose, keep `validation` as the technical term).
- Table cells that contain descriptions/explanations.

**Keep exactly as-is (do NOT translate):**
- **Filenames** — same name in the output folder.
- **Fenced code blocks** (```` ```…``` ````) — copy verbatim, including any code
  comments. Code is code.
- **Inline code** in backticks — `RequestHandler`, `pip install treecap`,
  `src/server/handler.py`.
- **Identifiers and symbols** — class/function/variable names, module paths,
  file paths, line references like `handler.py:42`.
- **Library, framework, tool, and product names** — `FastAPI`, `Pydantic`,
  `React`, `PostgreSQL`, `treecap`.
- **Established technical terms** — keep them in English inline within the
  translated sentence (e.g. dependency injection, middleware, registry pattern,
  endpoint, schema, async). These are the shared vocabulary engineers use
  regardless of spoken language; translating them adds confusion, not clarity.
- **URLs, commands, and config snippets.**

### Example (English → Chinese)

Source (`01_architecture.md`):

````markdown
The central request handler lives in `src/server/handler.py`. Every inbound
request flows through `handle()`: it authenticates the caller, loads the
relevant record, and renders a response. Note the dependency injection in
`__init__` — `Store` and `AuthService` are passed in rather than constructed
here, which makes the handler unit-testable.

```python
async def handle(self, req: Request) -> Response:
    user = await self.auth.verify(req.token)
    return self._render(record, user)
```
````

Translated (`01_architecture.md` inside `CODE_EXPLANATION_ZH/`):

````markdown
核心的 request handler 位于 `src/server/handler.py`。每个进入的请求都会经过
`handle()`：它会对调用方进行认证，加载相关的 record，然后渲染出 response。注意
`__init__` 中使用了 dependency injection —— `Store` 和 `AuthService` 是被传入的，
而不是在这里构造的，这使得该 handler 可以进行单元测试。

```python
async def handle(self, req: Request) -> Response:
    user = await self.auth.verify(req.token)
    return self._render(record, user)
```
````

Notice: the code block is byte-for-byte identical, all backticked identifiers
stay English, technical terms (`handler`, `dependency injection`, `record`,
`response`) stay English inline, and only the connective prose is translated.

## Quick checklist

- [ ] Determined the mode: whole folder, or a single file
- [ ] Resolved target language code (Chinese/`ZH` by default)
- [ ] **Folder mode:** created `<FOLDER>_<CODE>/` sibling, one output file per source file with **identical filenames**
- [ ] **Single file < 50 lines:** edited in place, bilingual (English line then translation line), code blocks kept once
- [ ] **Single file ≥ 50 lines:** wrote a `<name>_<lang>.<ext>` sidecar in the same folder, original untouched
- [ ] Prose translated; code blocks, identifiers, paths, and tool/library names verbatim
- [ ] Technical terms kept in English inline within translated sentences
