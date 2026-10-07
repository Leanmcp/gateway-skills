# Security Policy

## Reporting a vulnerability

Please **do not open a public GitHub issue** for security problems.

Report vulnerabilities privately through one of these channels:

- GitHub: use [Report a vulnerability](https://github.com/Leanmcp/superview.sh/security/advisories/new) on this repository (private security advisory).

Please include:

- What the issue is and where it lives (file, skill, or gateway endpoint)
- Steps to reproduce, or a minimal proof of concept
- The impact you expect (data exposure, key leakage, privilege escalation, etc.)

## What to expect

- We acknowledge reports within **3 business days**.
- We aim to share an initial assessment within **7 days**.
- We will keep you updated until the issue is fixed and credit you in the advisory unless you prefer to stay anonymous.

## Scope

In scope:

- Content in this repository, including the skills under `skills/` and `claude-code-skills/`
- Secrets or credentials accidentally committed to this repository
- The Leanmcp AI Gateway (`aigateway.leanmcp.com`) and dashboard (`app.leanmcp.com`)

Out of scope:

- Vulnerabilities in third-party tools listed in the README guide. Please report those to the upstream project.
- Social engineering, physical attacks, and denial-of-service testing

## Handling secrets

Never commit API keys, tokens, or account identifiers. Skills in this repo reference credentials only by environment variable name (for example `ANTHROPIC_API_KEY`) or by placeholder (for example `<TEAM_ID>`). If you spot a real credential, report it privately using the channels above.
