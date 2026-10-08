# django-skills

A focused collection of Django skills for [Claude Code](https://claude.ai/code), installable
via the [vercel-labs/skills](https://github.com/vercel-labs/skills) CLI.

This repo used to host a wider range of skills (API-wrapping tools alongside Django recipes).
Maintaining a broad catalogue well costs more than it's worth, and most of those skills added
limited value beyond "ships quick"; it's narrower now, covering Django specifically, where
there's a coherent, maintainable set of idioms, a code review process, and a project scaffold
that reinforce each other.

All skills here are **recipes**: opinionated starting points, not maintained tools. They encode
a specific way of doing something — idioms to apply while writing code, a review process, a
project scaffold — and are designed to be **copied and adapted** rather than relied on for
updates.

Install a recipe, use it as a baseline, and then edit your local copy to match your environment
and conventions. A recipe you've tailored to your project is more valuable than one you depend
on staying up to date.

| Skill | Description |
|---|---|
| [`django-development`](django-development/) | General Django idioms for models, views, templates, and tests — each rule stated as a Do/Why/Except to apply while generating code |
| [`celery`](celery/) | Celery idioms for Django projects — task argument serialisation and concurrency rules, layered above `django-development` |
| [`django-layout`](django-layout/) | Scaffold a production-ready Django project with uv, Docker, and PostgreSQL — asks which optional add-ons (Celery, S3, auth, htmx, Sentry, dev tools) to include before generating |
| [`django-code-review`](django-code-review/) | Structured Django code review using focused playbooks (Do/Why/Except/Evidence rule cards) for migrations, querysets, signals, Celery, security, and more |

`django-development` and `celery` share a precedence model with each other and with your own
project conventions: project-specific rules override package-specific ones (`celery`), which
override general framework idioms (`django-development`). `django-code-review`'s playbooks
reference both directly where a review check is the same underlying rule applied at review
time rather than write time.

---

## Installing a skill

```bash
# Install a single skill into the current project
npx skills add lincoln-loop/django-skills --skill django-development

# Install globally (available in every project)
npx skills add lincoln-loop/django-skills --skill django-development --global

# Interactive — choose skills, target agents, and install mode
npx skills add lincoln-loop/django-skills

# Non-interactive (CI / scripted)
npx skills add lincoln-loop/django-skills --skill django-development -a claude-code -y
```

### Prerequisites

- Node.js ≥ 18

---

## Contributing

Contributions are welcome, within scope: Django idioms, review playbooks, and project-scaffold
improvements. There is no fixed template; see any existing skill for the shape to follow —
`SKILL.md` + `README.md`, and `references/` for a playbook-based skill like
`django-code-review`. No scripts or tests required for a recipe.

Open a pull request with your skill in its own top-level directory. Add a row to the table in
this README so it shows up in the index.
