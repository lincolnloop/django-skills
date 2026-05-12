# Django Layout Recipe

A recipe for generating a production-ready Django project. When installed and activated, Claude
will scaffold a complete project with the full directory structure, configuration files, Docker
setup, and tooling wired together.

> **This is a recipe, not a tool.** It will not be kept in sync with the latest Django release
> or dependency versions. Treat it as an opinionated starting point you copy and adapt for your
> own environment. The best outcome is a version of this skill tailored to your team's stack and
> conventions, not continued reliance on updates from this project.

## Stack

| Layer | Choice |
|---|---|
| Runtime | Python 3.13, [uv](https://docs.astral.sh/uv/) |
| Framework | Django + django-environ, django-allauth, django-htmx |
| Database | PostgreSQL 17 |
| Cache / queue | Redis 7, Celery |
| Storage | django-storages (S3) + whitenoise |
| Monitoring | django-health-check, Sentry |
| Infrastructure | Docker Compose (web / db / redis / celery) |
| Quality | ruff, ty, pre-commit |

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

## Customising for your environment

This recipe reflects one opinionated setup. Common things to change:

- **Remove packages you don't need** — strip `celery`/`redis` if you don't use background
  tasks, remove `django-storages`/`boto3` if you're not using S3.
- **Swap the auth approach** — replace `django-allauth` with your preferred auth package or a
  custom implementation.
- **Adjust the settings strategy** — the single `config/settings.py` gated by `DJANGO_ENV`
  works well but some teams prefer environment-specific files.
- **Update dependency versions** — pin the `ruff` pre-commit revision and check for newer
  Django and Postgres base images before using this on a real project.
- **Add your own apps** — extend the `apps/` layout with whatever domain apps your project
  needs from the start.

The best approach is to install the skill, run it once on a scratch project, review what was
generated, and then edit your local copy of `SKILL.md` to match your preferences.

## Prerequisites

- Node.js ≥ 18 (for the `npx skills` CLI)
- [uv](https://docs.astral.sh/uv/) installed on the machine where you run Claude Code
- Docker and Docker Compose for the generated project
