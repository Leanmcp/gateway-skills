# Style: builder technical

Engineer to engineer. Assumes the reader knows the domain and would be insulted by having it explained. The register of a good commit message, a Hacker News comment, or a README written by someone who actually uses the tool.

## Core principle

Respect the reader's time by assuming competence. No "as you may know", no defining terms the audience uses daily, no benefits framing. State what it does, how, and where it breaks.

The implicit contract is: I will not waste your time, and in exchange you will take the claim seriously.

## Rules

- Lead with the mechanism, not the benefit. "Batches embedding calls into groups of 64" beats "dramatically improves performance".
- Numbers with units and conditions. "240ms p99 on a single A10G, batch size 64" not "much faster".
- Name the actual technologies, versions, and constraints.
- Say what it does not do, early and plainly. This is the strongest credibility move available in technical writing.
- Comparisons should be fair. If you benchmark against an alternative, state its configuration. Technical readers check, and being caught with a rigged comparison ends the conversation permanently.
- Code and commands inline, in backticks or fenced blocks.
- No marketing adjectives at all. Not "powerful", not "blazing fast", not "production-ready" unless you can say what that means.
- Sentence case or lowercase, either works. Match the platform.
- Hedge accurately rather than confidently. "This should work for single-file repos, I haven't tested monorepos" is better writing than either overclaiming or vague hedging.

## Things this style does that others don't

**Show the artifact.** A terminal screenshot, a diff, a flamegraph, a log line. Technical audiences trust an artifact more than a sentence.

**Include the install line.** Make it trivially easy to try. `uv add x` or `npx y` in the post itself.

**Post the failure.** "First approach was one jsonl per run. Useless, you can't read a 400MB jsonl and you can't diff two of them." This is the most valuable content in a technical post and the part generated copy never has.

**Anticipate the obvious objection.** If everyone's first reaction will be "why not just use OpenTelemetry", answer that in the post. Otherwise you spend the comments answering it one person at a time.

## Example

```
Traces for agent evals, written per-episode as the run happens.

Each episode gets a directory: one JSON per turn with the tool calls, their
arguments and results, the reasoning trace if the provider returns one, and
token counts. Plus whatever artifacts the task produced.

First version wrote one JSONL per run. Don't do this. A 400MB JSONL is not
readable and two of them are not diffable.

Why not OpenTelemetry: we tried. Spans model request/response well and model
"the agent read a file, thought about it, and revised its plan" badly. We
ended up stuffing everything into span attributes and reading raw JSON anyway.

Runs ~40 episodes in parallel on one machine, limited by provider rate limits
rather than local CPU. Viewer is a TUI.

Not solved: cross-provider diffing. OpenAI and Anthropic trace shapes differ
enough that every unified schema we tried drops something real from one side.

  uv add <pkg>

<repo link>
```

## Where it fits

| Platform | Fit |
|---|---|
| Hacker News | default |
| Developer Discords | default |
| X / Twitter (dev audience) | default, often combined with lowercase |
| GitHub README, release notes | default |
| Medium / Substack technical posts | default for the body |
| LinkedIn | works for an engineering audience, soften slightly |
| Instagram | no |
