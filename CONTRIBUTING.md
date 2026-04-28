# Contributing

Thanks for helping out. Contributions of all sizes are welcome: typo fixes, new tools for the guide, new skills, and improvements to existing ones.

## Quick workflow

1. Fork the repo and create a branch: `git checkout -b my-change`
2. Make your change.
3. Run the README check: `sh tests/check-readme-repo-metrics.sh`
4. Open a pull request with a short description of what changed and why.

Keep PRs focused. One tool, one skill, or one fix per PR makes review fast.

## Adding a tool to the guide

- Add a section under **Featured Open-Source AI Coding Assistants** that follows the existing format (GitHub link, what makes it special, best for, license).
- Add a row to the **Comparison Table**.
- Only list tools that are open source and actively maintained.

## Adding or updating a skill

Skills live in `skills/<skill-name>/` and follow the Claude Code skill layout:

```
skills/<skill-name>/
├── SKILL.md          # required: frontmatter (name, description) + instructions
├── references/       # optional: longer docs loaded on demand
└── scripts/          # optional: helper scripts
```

Before you open the PR:

- The `name` in `SKILL.md` frontmatter matches the folder name.
- The `description` says what the skill does **and** when it should trigger.
- **No secrets or personal identifiers.** Use environment variable names (`FIREWORKS_API_KEY`) or placeholders (`<TEAM_ID>`, `<your-account-id>`), never real values. No absolute paths from your machine.
- Add a row for the skill to [`skills/README.md`](./skills/README.md).

## Commit messages

Use short, imperative messages with a conventional prefix:

```
docs: add Goose to comparison table
feat(skills): add mcp-builder skill
fix: correct star-history link
```

## Code of conduct

Be respectful and constructive. Harassment or personal attacks are not tolerated in issues, PRs, or Discord.

## Security

Found a vulnerability? Please follow [SECURITY.md](./SECURITY.md) and do not file a public issue.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](./LICENSE).
