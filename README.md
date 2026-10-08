# agent-skills

A collection of skills for [Claude Code](https://claude.ai/code), installable via the
[vercel-labs/skills](https://github.com/vercel-labs/skills) CLI.

Skills come in two kinds: **tools** and **recipes**. They are installed the same way, but they
serve different purposes and age differently.

---

## Tools

Tools wrap external APIs. Each tool ships Python scripts with structured JSON output, JSON
schemas describing that output, and a test suite. They are maintained as the APIs evolve.

| Skill | Description |
|---|---|
| [`harvest`](harvest/) | Harvest API v2 — time entries, reports, invoices, expenses, and account data |
| [`parallax-insights`](parallax-insights/) | Parallax Insights API — time entries, allocations, people financials, project financials, and pipeline data |
| [`slack`](slack/) | Slack Web API — send messages, post Block Kit reports, read channels, and list workspace members |
| [`statuscake`](statuscake/) | StatusCake API v1 — uptime, SSL, pagespeed, heartbeat, and account configuration |
| [`logseq`](logseq/) | Logseq HTTP API — read and write pages and blocks in a local Logseq graph |

## Recipes

Recipes are opinionated starting points, not maintained tools. They encode a specific way of
doing something — a project scaffold, a review process, a workflow — and are designed to be
**copied and adapted** rather than relied on for updates.

Install a recipe, use it as a baseline, and then edit your local copy to match your environment
and conventions. A recipe you've tailored to your project is more valuable than one you depend
on staying up to date.

| Skill | Description |
|---|---|
| [`django-layout`](django-layout/) | Scaffold a production-ready Django project with uv, Docker, PostgreSQL, Redis, Celery, and htmx |
| [`django-code-review`](django-code-review/) | Structured Django code review using focused playbooks for migrations, querysets, signals, Celery, security, and more |
| [`django-development`](django-development/) | General Django idioms for models, views, templates, and tests — each rule stated as a Do/Why/Except to apply while generating code |
| [`celery`](celery/) | Celery idioms for Django projects — task argument serialisation and concurrency rules, layered above `django-development` |

---

## Installing a skill

```bash
# Install a single skill into the current project
npx skills add lincoln-loop/agent-skills --skill harvest

# Install globally (available in every project)
npx skills add lincoln-loop/agent-skills --skill harvest --global

# Interactive — choose skills, target agents, and install mode
npx skills add lincoln-loop/agent-skills

# Non-interactive (CI / scripted)
npx skills add lincoln-loop/agent-skills --skill harvest -a claude-code -y
```

### Prerequisites

- Node.js ≥ 18
- [uv](https://docs.astral.sh/uv/) (for running the tool scripts)

---

## Running tests (tools only)

Each tool skill has a test suite. Unit tests run without credentials; integration tests require
a live API connection and are automatically skipped when credentials are absent.

```bash
# Unit tests only
cd harvest
uv run --with pytest --with requests pytest tests/test_lib.py -v

# All tests (integration tests skipped when credentials are missing)
uv run --with pytest --with requests pytest tests/ -v
```

---

## Contributing

All contributions are welcome — tools, recipes, or anything in between. The purpose of this
project is to share skills, knowledge, and ideas about what AI agents can do. There is no fixed
template; bring whatever is useful.

A few loose guidelines:

- **Tools** (API integrations) are most useful with a shared library, structured JSON output,
  and a test suite so others can verify they work. See any of the existing tool skills for
  reference.
- **Recipes** (scaffolds, workflows, review processes) need only a `SKILL.md` and a `README.md`
  explaining what the recipe does and how to adapt it. No scripts or tests required.
- **Anything else** — if it helps you work with an AI agent more effectively and you think
  others might benefit, it belongs here.

Open a pull request with your skill in its own top-level directory. Add a row to the relevant
table in this README so it shows up in the index.
