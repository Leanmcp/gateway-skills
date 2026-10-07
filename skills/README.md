# Skills

Claude Code skills used by the Leanmcp team. Each folder is a self-contained skill with a `SKILL.md` at its root.

## Install

Copy any skill folder into your Claude Code skills directory:

```bash
cp -r skills/mcp-builder ~/.claude/skills/
```

Claude Code picks it up on the next session and triggers it automatically when the task matches the skill's description.

## Index

### MCP development

| Skill | What it does |
|-------|--------------|
| [leanmcp-builder](./leanmcp-builder/) | Build MCP servers with the Leanmcp SDK's decorator-based TypeScript: auth, elicitation, env injection. |
| [mcp-apps-builder](./mcp-apps-builder/) | Build MCP Apps with interactive React UIs using the Leanmcp UI SDK. |
| [mcp-builder](./mcp-builder/) | Build MCP servers with the official `@modelcontextprotocol/sdk` over Streamable HTTP. |

### Inference, training and evaluation

| Skill | What it does |
|-------|--------------|
| [fireworks-inference](./fireworks-inference/) | Run inference on Fireworks AI directly or through the Leanmcp AI Gateway for observability. |
| [tinker-training-inference](./tinker-training-inference/) | LoRA and full fine-tuning, SFT and RL on Tinker, plus checkpoints and cost estimates. |
| [research-observability](./research-observability/) | File-based tracing, transcripts and run comparison for LLM and agent experiments. |
| [analyze-exports](./analyze-exports/) | Pinpoint where and why tau2-bench tasks failed from export files. |

### Security

| Skill | What it does |
|-------|--------------|
| [security-repro](./security-repro/) | Safe, offline reproductions of already-patched, publicly disclosed vulnerabilities. |
| [vuln-repro](./vuln-repro/) | End-to-end methodology for reproducing and patching disclosed CVEs, through to the write-up. |

### Docs and writing

| Skill | What it does |
|-------|--------------|
| [code-explanation](./code-explanation/) | Generate a beginner-friendly `CODE_EXPLANATION/` walkthrough of any repo. |
| [translate-explanation](./translate-explanation/) | Translate code-explanation docs into another language (Chinese by default). |
| [research-paper-integrity](./research-paper-integrity/) | Writing standards and citation audits for ML/NLP paper submissions. |
| [publicity-distribution](./publicity-distribution/) | Launch copy for LinkedIn, X, Discord, Medium and YouTube that doesn't read as AI-written. |

### Apps and games

| Skill | What it does |
|-------|--------------|
| [ios-bootstrap-testflight](./ios-bootstrap-testflight/) | Scaffold a SwiftUI app and ship it to TestFlight entirely from the CLI. |
| [godot-city-game-3d](./godot-city-game-3d/) | Build, debug and ship procedural 3D city games in Godot 4. |
| [posthog-adblock-bypass](./posthog-adblock-bypass/) | Keep posthog-js session replay working in Next.js when ad blockers block its scripts. |

## Credentials

No skill in this folder contains real credentials. Skills reference keys only by environment variable name (for example `FIREWORKS_API_KEY`). Where account-specific values are needed, they appear as placeholders like `<TEAM_ID>`, which you fill in locally.
