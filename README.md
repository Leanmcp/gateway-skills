<div align="center">

# Leanmcp Skills & AI Gateway

### See everything your AI coding agent sends. Every request, every file, every token.

[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?style=flat-square&logo=discord&logoColor=white)](https://discord.com/invite/DsRcA3GwPy)
[![Follow on X](https://img.shields.io/badge/X-@paidev-000000?style=flat-square&logo=x&logoColor=white)](https://x.com/paidev)
[![Stars](https://img.shields.io/github/stars/Leanmcp/superview.sh?style=flat-square&color=yellow)](https://github.com/Leanmcp/superview.sh/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](./LICENSE)

[Website](https://leanmcp.com/ai-gateway?utm_source=superview&utm_medium=github&utm_campaign=readme) · [Docs](https://docs.leanmcp.com/ai-gateway/claude-code) · [Dashboard](https://app.leanmcp.com)

---

</div>

This repository brings together [Leanmcp skills](./skills/README.md), AI Gateway setup, and an open-source AI coding guide. The skills cover MCP development, inference and training, research, security, and documentation workflows.

## What is the Leanmcp AI Gateway?

The Leanmcp AI Gateway is a drop-in proxy that sits between your AI coding agent (Claude Code, or anything that speaks the Anthropic or OpenAI API) and the model provider. You change one URL, and every request shows up in your dashboard:

- **Full request and response logs.** See the exact prompts, system prompts and tool calls your agent sends.
- **File visibility.** See which files the agent read and what it pulled into context.
- **Token and cost tracking.** Per request, per session and per project.
- **No code changes.** It's one environment variable. Your agent keeps working exactly as before.

## Quick start: Claude Code

Two lines give you full visibility into what Claude Code is doing:

```bash
export ANTHROPIC_BASE_URL=https://aigateway.leanmcp.com/v1/anthropic
export ANTHROPIC_API_KEY=your_leanmcp_key
```

1. Get your key at [app.leanmcp.com/billing](https://app.leanmcp.com/billing).
2. Run any Claude Code task.
3. Open [app.leanmcp.com](https://app.leanmcp.com) to see the logs.

Full setup guide: [docs.leanmcp.com/ai-gateway/claude-code](https://docs.leanmcp.com/ai-gateway/claude-code)

## What's in this repo

| Path | What it is |
|------|------------|
| [`skills/`](./skills/) | Claude Code skills we use day to day: MCP server builders, inference and training workflows, research tooling, and more. See the [skills index](./skills/README.md). |
| [`claude-code-skills/`](./claude-code-skills/) | A style-guide skill for contributing to the Claude Code codebase. |
| [Open-source AI coding guide](#featured-open-source-ai-coding-assistants) | A comparison of the best open-source AI coding assistants (below). |

---

## Table of Contents

- [What is the Leanmcp AI Gateway?](#what-is-the-leanmcp-ai-gateway)
- [Quick start: Claude Code](#quick-start-claude-code)
- [What's in this repo](#whats-in-this-repo)
- [Why Open Source Matters for AI Coding](#why-open-source-matters-for-ai-coding)
- [Featured Open-Source AI Coding Assistants](#featured-open-source-ai-coding-assistants)
  - [Cline](#1-cline)
  - [OpenCode](#2-opencode)
  - [OpenHands (by AllHands AI)](#3-openhands-by-allhands-ai)
  - [Aider](#4-aider)
  - [Continue](#5-continue)
  - [Tabby](#6-tabby)
  - [Void](#7-void)
  - [Goose (by Block)](#8-goose-by-block)
  - [Cursor Open Source Alternatives](#9-cursor-open-source-alternatives)
- [Comparison Table](#comparison-table)
- [How to Choose the Right Tool](#how-to-choose-the-right-tool)
- [The Rise of Agentic Coding](#the-rise-of-agentic-coding)
- [Self-Hosting vs Cloud](#self-hosting-vs-cloud)
- [Claude Code Skills Package](#claude-code-skills-package)
- [Community & Contributing](#community--contributing)
- [Resources & Further Reading](#resources--further-reading)
- [Star History](#star-history)

---

## Quick Start

Want to try one right now? Here are the fastest way to get started with the top tools:

```bash
# Aider — pip install and go
pip install aider-chat
aider

# OpenCode — single binary
curl -fsSL https://opencode.ai/install | sh
opencode

# Cline — install from VS Code marketplace
# Search "Cline" in VS Code extensions

# Goose — install via pipx
pipx install goose-ai
goose session start
```

---

## Why Open Source Matters for AI Coding

The world of software development is undergoing a seismic transformation. AI-powered coding assistants have gone from novelty to necessity in an incredibly short time. Tools like GitHub Copilot, Cursor, and various proprietary CLI agents have demonstrated that AI can dramatically accelerate development workflows — from writing boilerplate code to debugging complex systems to refactoring entire codebases.

But here's the problem: **most of these tools are closed-source.**

That means:

- **No transparency.** You don't know what data is being collected, how your code is being processed, or what happens to your proprietary business logic when it's sent to a remote server.
- **Vendor lock-in.** Your entire workflow becomes dependent on a single company's pricing decisions, uptime, and continued existence.
- **No customization.** You can't adapt the tool to your specific needs, integrate it with your internal systems, or fix bugs that affect your team.
- **Privacy concerns.** For enterprises working with sensitive code — healthcare, finance, defense, legal — sending code to third-party servers is often a non-starter.
- **Cost at scale.** Per-seat pricing for AI tools can become astronomical for large teams, especially when usage is heavy.

**Open-source AI coding assistants solve all of these problems.** They give you full control over your data, your infrastructure, and your workflow. You can self-host them, audit their code, customize their behavior, and contribute improvements back to the community.

The open-source ecosystem for AI coding tools has exploded in 2025–2026. What was once a barren landscape with a few experimental projects is now a thriving ecosystem of production-ready tools that rival — and in many cases surpass — their proprietary counterparts.

This guide is here to help you navigate this ecosystem.

---

## Featured Open-Source AI Coding Assistants

### 1. Cline

**GitHub:** [cline/cline](https://github.com/cline/cline)

Cline is one of the most popular open-source AI coding assistants in the VS Code ecosystem. Originally known as "Claude Dev," Cline has evolved into a fully autonomous coding agent that lives inside your editor.

**What makes Cline special:**

- **Agentic workflow.** Cline doesn't just suggest code — it can create and edit files, run terminal commands, use the browser, and execute multi-step tasks autonomously. You approve each action through a human-in-the-loop GUI, so you're always in control.
- **Model-agnostic.** Cline works with any LLM provider — OpenAI, Anthropic, Google, Mistral, local models via Ollama or LM Studio, or any OpenAI-compatible API. You're never locked into a single AI provider.
- **MCP support.** Cline has first-class support for the Model Context Protocol (MCP), which means it can connect to external tools, databases, APIs, and services through a standardized interface. This makes it incredibly extensible.
- **Context-aware.** Cline can read your entire project structure, understand file relationships, parse error messages, and use that context to make intelligent decisions about what to change and how.
- **Browser integration.** Cline can launch a browser, take screenshots, click elements, and test web applications — all from within VS Code. This is incredibly powerful for frontend development and debugging.

**Best for:** Developers who want a powerful, autonomous coding agent directly in VS Code with full control over which LLM they use.

**License:** Apache 2.0

---

### 2. OpenCode

**GitHub:** [opencode-ai/opencode](https://github.com/opencode-ai/opencode)

OpenCode is a modern, terminal-native AI coding assistant built for developers who live in the command line. It provides a beautiful TUI (Terminal User Interface) that makes interacting with AI feel natural and fast.

**What makes OpenCode special:**

- **Terminal-first design.** OpenCode is built from the ground up for the terminal. It has a gorgeous, responsive TUI built with Bubble Tea that feels like a first-class application, not a hacky CLI tool.
- **LSP integration.** OpenCode connects to your Language Server Protocol, giving it deep understanding of your codebase — types, definitions, references, diagnostics, and more. This means it can provide much more accurate and contextual assistance than tools that just read raw files.
- **Multi-provider support.** Works with Anthropic, OpenAI, Google Gemini, AWS Bedrock, Azure OpenAI, Groq, OpenRouter, and any OpenAI-compatible provider.
- **Session management.** OpenCode maintains conversation sessions, so you can continue where you left off, revisit past conversations, and manage multiple threads of work simultaneously.
- **Git-aware.** OpenCode understands your git history and can use diffs, blame, and log information to provide better context for its suggestions.
- **Customizable tools.** You can extend OpenCode with custom tools and plugins to match your specific workflow.

**Best for:** Terminal-centric developers who want a fast, beautiful AI assistant that deeply integrates with their existing CLI workflow.

**License:** MIT

---

### 3. OpenHands (by AllHands AI)

**GitHub:** [All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands)

OpenHands (formerly OpenDevin) is one of the most ambitious open-source projects in the AI coding space. It's a platform for building **AI-powered software development agents** — not just coding assistants, but full-fledged autonomous agents that can handle complex software engineering tasks from start to finish.

**What makes OpenHands special:**

- **Autonomous agents.** OpenHands agents can browse the web, write code, run commands, interact with APIs, and perform multi-step reasoning — all autonomously. They're not just autocomplete on steroids; they're virtual software engineers.
- **Sandboxed execution.** All code execution happens in secure Docker sandboxes, so agents can safely run, test, and iterate on code without affecting your host system. This is critical for production use.
- **SWE-Bench performance.** OpenHands consistently ranks among the top performers on SWE-Bench, the industry-standard benchmark for AI software engineering. This means it can actually solve real GitHub issues, not just toy examples.
- **Web UI and CLI.** OpenHands offers both a beautiful web interface and a command-line interface, so you can interact with it however you prefer.
- **Multi-agent architecture.** OpenHands supports multiple agent architectures, including CodeAct (the default), which combines code execution with natural language reasoning for maximum effectiveness.
- **Enterprise-ready.** OpenHands can be self-hosted, supports multiple LLM backends, and has robust security features that make it suitable for enterprise deployments.
- **Active community.** With thousands of contributors and an incredibly active GitHub and Discord community, OpenHands is one of the fastest-evolving open-source projects in the AI space.

**Best for:** Teams and organizations that want a powerful, self-hosted AI software engineering platform capable of handling complex, multi-step tasks autonomously.

**License:** MIT

---

### 4. Aider

**GitHub:** [paul-gauthier/aider](https://github.com/paul-gauthier/aider)

Aider is the OG of AI pair programming in the terminal. Created by Paul Gauthier, Aider has been setting the standard for CLI-based AI coding assistants since early 2023. It's battle-tested, incredibly well-documented, and has one of the most thoughtful designs in the space.

**What makes Aider special:**

- **Git integration.** Aider automatically commits every change it makes with a sensible commit message. This means you always have a clean git history, and you can easily review, revert, or cherry-pick AI-generated changes. This is one of those features that sounds simple but is transformative in practice.
- **Multi-file editing.** Aider excels at making coordinated changes across multiple files. It understands your project structure and can refactor across module boundaries, update imports, and maintain consistency.
- **Repository mapping.** Aider builds a map of your entire repository using tree-sitter, understanding the structure of your codebase — classes, functions, methods, imports — so it can provide contextually relevant suggestions without you having to manually specify which files to include.
- **Benchmark leader.** Aider consistently performs at the top of AI coding benchmarks. Paul publishes detailed benchmark results on the Aider leaderboard, providing transparent comparisons of different LLMs on real coding tasks.
- **Voice coding.** Aider supports voice input, so you can literally talk to your code. This is incredibly useful for brainstorming, describing complex changes, or when you want to keep your hands free.
- **Model flexibility.** Works with virtually every major LLM provider and local models. Aider's model configuration is one of the most flexible in the ecosystem.
- **Linting and testing.** Aider can automatically lint your code after making changes and run your test suite to verify correctness. If tests fail, it can automatically attempt to fix the issues.

**Best for:** Developers who want a rock-solid, well-tested terminal AI assistant with exceptional git integration and multi-file editing capabilities.

**License:** Apache 2.0

---

### 5. Continue

**GitHub:** [continuedev/continue](https://github.com/continuedev/continue)

Continue is the leading open-source AI code assistant for IDEs. It's designed as a direct open-source alternative to GitHub Copilot, offering code completion, chat, and editing capabilities — all within VS Code and JetBrains IDEs.

**What makes Continue special:**

- **IDE-native experience.** Continue integrates deeply with VS Code and JetBrains IDEs, providing inline code completion (tab autocomplete), a chat sidebar, and inline editing commands — exactly like the proprietary tools you're used to.
- **Autocomplete.** Continue offers fast, context-aware tab autocomplete powered by any model you choose. You can use a fast local model (like Qwen, DeepSeek, or StarCoder) for autocomplete and a larger cloud model for chat — mixing and matching to optimize speed and quality.
- **Fully customizable.** Continue is designed around a `.continue/config.json` file that gives you fine-grained control over every aspect of the tool — models, context providers, slash commands, and more.
- **Context providers.** Continue has a rich plugin system for context providers that can pull in information from anywhere — your codebase, documentation, databases, Jira tickets, web search results, and more.
- **Local-first option.** Continue works beautifully with local models via Ollama, LM Studio, or llama.cpp. You can have a fully private, offline AI coding assistant with zero data leaving your machine.
- **Enterprise features.** Continue offers a paid enterprise tier with admin dashboards, usage analytics, and centralized configuration — but the core product is 100% open source.

**Best for:** Developers and teams looking for an open-source GitHub Copilot replacement with deep IDE integration and full model flexibility.

**License:** Apache 2.0

---

### 6. Tabby

**GitHub:** [TabbyML/tabby](https://github.com/TabbyML/tabby)

Tabby is a self-hosted AI coding assistant focused on being the open-source alternative to GitHub Copilot for enterprises. It's designed to be deployed on your own infrastructure, giving you complete control over your data and models.

**What makes Tabby special:**

- **Self-hosted by design.** Tabby is built from the ground up for self-hosting. It runs on your own servers (or even your local machine), ensuring that your code never leaves your network.
- **Code completion engine.** Tabby's core strength is its fast, high-quality code completion. It uses optimized inference to provide real-time suggestions as you type.
- **Repository-level context.** Tabby can index your entire codebase and use it as context for completions. This means it understands your project's patterns, conventions, and structures.
- **Admin dashboard.** Tabby includes a web-based admin dashboard for managing users, monitoring usage, and configuring the system.
- **GPU and CPU support.** Tabby can run on NVIDIA GPUs for maximum speed, Apple Metal, or even CPU-only for simpler deployments.
- **Multiple IDE support.** Works with VS Code, JetBrains IDEs, and Vim/Neovim.

**Best for:** Organizations that need a self-hosted, privacy-first code completion solution they can run entirely on their own infrastructure.

**License:** Apache 2.0

---

### 7. Void

**GitHub:** [voideditor/void](https://github.com/voideditor/void)

Void is an open-source code editor (fork of VS Code) that aims to be the open-source alternative to Cursor. If you love Cursor's AI-powered editing experience but want something you can customize, self-host, and control, Void is worth watching.

**What makes Void special:**

- **Full editor.** Unlike extensions that add AI to VS Code, Void IS the editor. This means AI is deeply integrated into every aspect of the editing experience — not bolted on as an afterthought.
- **Cursor-like experience.** Void offers inline editing, chat, and code generation features similar to Cursor, but with full transparency and no vendor lock-in.
- **Local model support.** Void is designed to work with local models, making it ideal for developers who want a fully offline AI coding experience.
- **Extensible.** Since Void is based on VS Code, it's compatible with the vast VS Code extension ecosystem.

**Best for:** Developers who want a Cursor-like experience in a fully open-source editor they can customize and self-host.

**License:** Apache 2.0

---

### 8. Goose (by Block)

**GitHub:** [block/goose](https://github.com/block/goose)

Goose is an open-source AI coding agent developed by Block (formerly Square). It's a semi-autonomous developer agent that can perform a wide range of tasks — from writing code to managing infrastructure.

**What makes Goose special:**

- **Backed by Block.** Goose is developed and maintained by Block, one of the largest fintech companies in the world. This means it has serious engineering resources and long-term viability behind it.
- **Extensible toolkit.** Goose has a modular toolkit architecture that lets you add new capabilities easily. It can interact with GitHub, Jira, Slack, databases, and virtually any API.
- **Session management.** Goose maintains conversation sessions and can resume work across multiple interactions, making it ideal for complex, multi-day tasks.
- **MCP support.** Goose supports the Model Context Protocol, allowing it to connect to a growing ecosystem of external tools and data sources.
- **Multi-provider.** Works with multiple LLM providers, giving you flexibility in choosing your AI backend.

**Best for:** Developers and teams looking for a well-backed, extensible AI agent with strong tooling integration.

**License:** Apache 2.0

---

### 9. Cursor Open-Source Alternatives

Beyond the tools listed above, there's a growing ecosystem of open-source projects aiming to replicate and surpass the Cursor experience:

- **[Zed](https://github.com/zed-industries/zed)** — A blazing-fast code editor built in Rust with AI features built in. Open source, performant, and beautiful.
- **[Aide](https://github.com/codestoryai/aide)** (by CodeStory) — An AI-native IDE built on VS Code with deep agentic capabilities.
- **[PearAI](https://github.com/trypear/pearai-master)** — An open-source AI code editor focused on making AI pair programming accessible and intuitive.
- **[Melty](https://github.com/meltylabs/melty)** — An AI code editor designed around the concept of "understanding your codebase" to provide more relevant assistance.
- **[Amp](https://github.com/nichochar/amp)** — Terminal-based AI coding agent with focus on speed and simplicity. Built in Rust for fast startup.
- **[Codex](https://github.com/openai/codex)** (by OpenAI) — OpenAI's open-source coding agent that run in the terminal. Uses OpenAI models with sandboxed code execution.

---

## Comparison Table

| Tool | Type | Interface | Stars | Self-Hosted | MCP | Local Models | Built With | License |
|------|------|-----------|:-----:|-------------|-----|--------------|------------|---------|
| **Cline** | Agent | VS Code Extension | ![](https://img.shields.io/github/stars/cline/cline?style=flat&label=) | N/A | Yes | Yes | TypeScript | Apache 2.0 |
| **OpenCode** | Assistant | Terminal (TUI) | ![](https://img.shields.io/github/stars/opencode-ai/opencode?style=flat&label=) | Yes | Yes | Yes | Go | MIT |
| **OpenHands** | Platform | Web UI + CLI | ![](https://img.shields.io/github/stars/All-Hands-AI/OpenHands?style=flat&label=) | Yes | Yes | Yes | Python | MIT |
| **Aider** | Assistant | Terminal (CLI) | ![](https://img.shields.io/github/stars/paul-gauthier/aider?style=flat&label=) | N/A | No | Yes | Python | Apache 2.0 |
| **Continue** | Assistant | VS Code / JetBrains | ![](https://img.shields.io/github/stars/continuedev/continue?style=flat&label=) | Yes | Yes | Yes | TypeScript | Apache 2.0 |
| **Tabby** | Completion | VS Code / JetBrains / Vim | ![](https://img.shields.io/github/stars/TabbyML/tabby?style=flat&label=) | Yes | No | Yes | Rust | Apache 2.0 |
| **Void** | Editor | Standalone (VS Code fork) | ![](https://img.shields.io/github/stars/voideditor/void?style=flat&label=) | Yes | No | Yes | TypeScript | Apache 2.0 |
| **Goose** | Agent | Terminal (CLI) | ![](https://img.shields.io/github/stars/block/goose?style=flat&label=) | N/A | Yes | Yes | Rust | Apache 2.0 |

---

## How to Choose the Right Tool

Choosing the right AI coding assistant depends on your specific needs, workflow, and constraints. Here's a decision framework:

### You want an AI agent in VS Code → **Cline**
If you live in VS Code and want a powerful autonomous agent that can create files, run commands, and browse the web — all with human-in-the-loop approval — Cline is your best bet. It's the most feature-rich VS Code AI agent available.

### You want a terminal-based assistant → **Aider** or **OpenCode**
If the terminal is your home, both Aider and OpenCode are excellent choices. Aider is more mature, has superior git integration, and excels at multi-file editing. OpenCode has a more modern TUI, LSP integration, and session management. Try both and see which clicks.

### You want a full AI software engineering platform → **OpenHands**
If you need something that goes beyond simple code suggestions — an agent that can autonomously research, plan, code, test, and iterate — OpenHands is the most powerful option. It's especially valuable for teams that want to automate repetitive engineering tasks at scale.

### You want a Copilot replacement → **Continue** or **Tabby**
If your primary need is fast, inline code completion (tab autocomplete) and you want to replace GitHub Copilot, Continue and Tabby are your best options. Continue is more flexible with its model and context configuration. Tabby is more focused on self-hosted enterprise deployments.

### You want a full AI-powered editor → **Void** or **Zed**
If you want the AI baked directly into your editor (like Cursor does), Void and Zed are worth exploring. Void gives you a Cursor-like experience in an open-source package. Zed gives you blazing performance with AI features built in natively.

### You want a corporate-backed agent → **Goose**
If long-term maintenance and stability matters to you, Goose is backed by Block (formerly Square) with dedicated engineering resources. It has strong MCP support and extensible toolkit architecture that can connect to your existing tools.

### You want enterprise/team features → **OpenHands**, **Tabby**, or **Continue**
For enterprise deployments, you want tools with admin dashboards, usage monitoring, centralized configuration, and robust self-hosting support. OpenHands, Tabby, and Continue all offer enterprise-grade features.

---

## The Rise of Agentic Coding

We're witnessing a fundamental shift in how developers interact with AI. The first wave of AI coding tools (2022–2023) was dominated by **code completion** — tools like GitHub Copilot that suggest the next line or block of code as you type.

The second wave (2024–2025) brought **chat-based assistants** — tools like ChatGPT, Claude, and Cursor's chat that let you have conversations about your code and request changes.

The third wave (2025–2026), which we're in now, is all about **agentic coding**. These are AI systems that don't just suggest or chat — they **act**. They can:

- **Read and understand** entire codebases
- **Plan** multi-step approaches to complex problems
- **Write code** across multiple files simultaneously
- **Execute commands** in the terminal
- **Run tests** and iterate based on results
- **Browse the web** for documentation and examples
- **Interact with APIs** and external services
- **Manage git** workflows including branching, committing, and creating PRs

This agentic paradigm is incredibly powerful, and the open-source community is leading the charge. Tools like Cline, OpenHands, Aider, and Goose are pushing the boundaries of what's possible with autonomous coding agents.

The key advantage of open-source in this space is **trust**. When an AI agent has the ability to execute code, run commands, and modify your filesystem, you need to be able to verify what it's doing. Open-source tools give you complete transparency into the agent's behavior, decision-making, and data handling.

---

## Self-Hosting vs Cloud

One of the biggest advantages of open-source AI coding tools is the ability to self-host. Here's when each approach makes sense:

### Self-Host When:
- **Privacy is critical.** Your code is proprietary, sensitive, or subject to regulatory requirements (HIPAA, SOC 2, GDPR, etc.).
- **You need full control.** You want to customize the tool, choose your own models, and manage your own infrastructure.
- **Cost optimization.** At scale, self-hosting with your own GPU infrastructure can be significantly cheaper than per-seat SaaS pricing.
- **Latency matters.** Running models locally or on nearby servers eliminates network latency to cloud providers.
- **Offline access.** You need AI assistance in environments without reliable internet access (air-gapped networks, travel, etc.).

### Use Cloud When:
- **Getting started quickly.** Cloud-hosted options let you start immediately without any infrastructure setup.
- **Small team.** For small teams, the operational overhead of self-hosting may not be worth it.
- **Frontier models.** If you need access to the latest and most powerful models (GPT-4, Claude 3.5 Opus, Gemini Ultra), cloud APIs are the only option for now.
- **Burst usage.** If your usage is sporadic, pay-per-use cloud pricing may be more economical than maintaining dedicated infrastructure.

### Recommended Self-Hosting Stack:
1. **Local inference:** [Ollama](https://ollama.com/) or [vLLM](https://github.com/vllm-project/vllm) for running models locally
2. **Models:** Qwen 2.5 Coder, DeepSeek Coder V3, Codestral, or StarCoder2 for code-specific tasks
3. **Code assistant:** Any of the tools listed above configured to use your local inference server
4. **Hardware:** NVIDIA RTX 4090 or better for the best experience, Apple Silicon M-series for portable development

---

## Claude Code Skills Package

This repo includes a **Claude Code skill** in the [`claude-code-skills/`](./claude-code-skills/) directory. It's a comprehensive style guide that teaches Claude how to work with the Claude Code codebase - covering TypeScript patterns, tool architecture, testing conventions, and more.

If you contribute to Claude Code itself, install this skill to ensure your AI-assisted changes match the existing codebase style. See the [skills README](./claude-code-skills/README.md) for installation instructions.

### More skills

The [`skills/`](./skills/) directory holds the skills the Leanmcp team uses every day, covering MCP server development, Fireworks and Tinker inference and training, research observability, security reproductions, and more. Copy any folder into `~/.claude/skills/` to use it. The [skills index](./skills/README.md) lists them all.

---

## Community & Contributing

This repo is a community-driven project maintained by [Leanmcp](https://leanmcp.com). We believe that the future of AI-assisted development should be open, transparent, and accessible to everyone.

### Join Our Community

- **Discord:** [Join the Leanmcp Discord](https://discord.com/invite/DsRcA3GwPy) — Chat with other developers, share your setups, get help, and stay updated on the latest in open-source AI coding.
- **X (Twitter):** Follow [@paidev](https://x.com/paidev) for the latest updates, hot takes, and discussions about open-source AI coding tools.

### How to Contribute

We welcome contributions of all kinds:

- **Add a tool.** Know of an open-source AI coding tool we missed? Open a PR or issue!
- **Update information.** Tools evolve fast. If any information here is outdated, please help us keep it current.
- **Share your experience.** Write about your experience using these tools. What worked? What didn't? Your real-world insights help everyone.
- **Spread the word.** Star this repo, share it with your team, and help us grow the community.

See [CONTRIBUTING.md](./CONTRIBUTING.md) for how to open a PR, and [SECURITY.md](./SECURITY.md) for how to report a vulnerability.

---

## Related Post

Check out the full story and discussion:

**[https://x.com/paidev/status/2039014896650858586?s=20](https://x.com/paidev/status/2039014896650858586?s=20)**

---

## Resources & Further Reading

Helpful resources for getting deeper into AI-assisted coding:

- **[SWE-Bench](https://www.swebench.com/)** — The standard benchmark for evaluating AI coding agents on real GitHub issues. Check how tools perform before choosing one.
- **[Aider Leaderboard](https://aider.chat/docs/leaderboards/)** — Detailed benchmark results comparing different LLMs on coding tasks. Updated regularly.
- **[Model Context Protocol](https://modelcontextprotocol.io/)** — The open standard that many tools use for connecting to external data sources and APIs.
- **[Ollama](https://ollama.com/)** — The easiest way to run local LLMs. Essential for self-hosting setups.
- **[vLLM](https://github.com/vllm-project/vllm)** — High-performance LLM inference server for production deployments.

### Leanmcp skills and documentation

- **[Skills index](./skills/README.md)** — Browse the available skills and installation instructions.
- **[Documentation and writing skills](./skills/README.md#docs-and-writing)** — Code explanations, translations, research-paper checks, and publishing workflows.
- **[Claude Code style-guide skill](./claude-code-skills/README.md)** — Repository-specific contribution guidance and setup.
- **[AI Gateway setup guide](https://docs.leanmcp.com/ai-gateway/claude-code)** — Connect Claude Code to the Leanmcp AI Gateway.
- **[Contributing guide](./CONTRIBUTING.md)** — Add skills, documentation, and other resources to this repository.

---

## Star History

<a href="https://www.star-history.com/?repos=Leanmcp%2Fsuperview.sh&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=Leanmcp/superview.sh&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=Leanmcp/superview.sh&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/image?repos=Leanmcp/superview.sh&type=date&legend=top-left" />
 </picture>
</a>

---

<div align="center">

If you have read till here, you definitely deserve some good stuff. Go to [app.leanmcp.com](https://app.leanmcp.com) and use coupon code LEANMCP26 at checkout to get $99 claude code tokens. You can use them in your claude code for free. You can observe your Claude sessions in [app.leanmcp.com](https://app.leanmcp.com).

More about this in the [Docs](https://docs.leanmcp.com/ai-gateway/claude-code)

**Made with love by the open-source community.**

[![Discord](https://img.shields.io/badge/Discord-Join%20Us-5865F2?style=flat-square&logo=discord&logoColor=white)](https://discord.com/invite/DsRcA3GwPy)
[![Follow on X](https://img.shields.io/badge/X-@paidev-000000?style=flat-square&logo=x&logoColor=white)](https://x.com/paidev)

</div>
