# Django Layout Recipe

A recipe for generating a production-ready Django project. Rather than a fixed template, it
works in two phases: it first asks which optional add-ons you want, then generates only the
core plus what you accepted. That avoids the usual template problem — a fixed stack means
your first few commits are spent ripping out packages you didn't want.

> **This is a recipe, not a tool.** It will not be kept in sync with the latest Django release
> or dependency versions. Treat it as an opinionated starting point you copy and adapt for your
> own environment. The best outcome is a version of this skill tailored to your team's stack and
> conventions, not continued reliance on updates from this project.

## Core (always generated)

| Layer | Choice |
|---|---|
| Runtime | Python 3.13, [uv](https://docs.astral.sh/uv/) |
| Framework | Django + django-environ |
| Database | PostgreSQL 17 |
| Static/media | whitenoise |
| Infrastructure | Docker Compose (web / db) |
| Quality | ruff, ty, pre-commit |

## Optional add-ons (asked about, not assumed)

| Add-on | Adds |
|---|---|
| Celery + Redis | Background tasks: `redis`/`celery` services, `config/celery.py` |
| django-storages + S3 | Production media/static storage via S3 |
| django-allauth | Authentication, with a `CustomAccountAdapter` extension point |
| django-htmx + Alpine.js | Interactive frontend: htmx middleware, a base template with a sidebar/hamburger menu |
| Sentry | Error monitoring, gated to production |
| django-health-check | A `/health/` endpoint |
| Dev tools | django-debug-toolbar, django-extensions, django-browser-reload (dev/test only) |

## Installation

```bash
npx skills add lincoln-loop/agent-skills --skill django-layout
```

Or globally:

```bash
npx skills add lincoln-loop/agent-skills --skill django-layout --global
```

Once installed, trigger it by asking Claude to:

> "Create a new Django project called myproject"

Claude will confirm the project name and ask which add-ons you want before generating anything.

## Customising for your environment

This recipe reflects one opinionated core, with pluggable add-ons grafted onto the same files
rather than maintained as separate variants. Common things to change:

- **Add your own add-on.** Follow the existing add-ons' shape in `SKILL.md`: what dependency it
  adds, what file(s) it touches, and what environment variables it needs.
- **Swap a core choice.** Postgres version, Python version, or the `DJANGO_ENV`-gated single
  settings file approach (some teams prefer environment-specific settings files) are all just
  edits to the core section.
- **Update dependency versions.** Pin the `ruff` pre-commit revision and check for newer Django
  and Postgres base images before using this on a real project.
- **Add your own apps.** Extend the `apps/` layout with whatever domain apps your project needs
  from the start.

The best approach is to install the skill, run it once on a scratch project with a couple of
different add-on combinations, review what was generated each time, and then edit your local
copy of `SKILL.md` to match your team's actual stack.

## Prerequisites

- Node.js ≥ 18 (for the `npx skills` CLI)
- [uv](https://docs.astral.sh/uv/) installed on the machine where you run Claude Code
- Docker and Docker Compose for the generated project
