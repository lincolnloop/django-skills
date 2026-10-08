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

## Using the skills

Installing a skill makes it *available*. Whether an agent actually uses it depends on which kind
of skill it is.

| Kind | Skills | Triggered by |
|---|---|---|
| **Task** | `django-code-review`, `django-layout` | What you ask for: "review this PR" matches the skill's description |
| **Background** | `django-development`, `celery` | The agent noticing, mid-task, that the code it's writing matches the skill's description |

Task skills rarely get missed, because your request names the task. Background skills are the
ones that can be skipped: nobody asks for them, so the agent has to make the connection itself.

### Make background skills dependable

Add a few lines to your project's always-loaded instructions file (`AGENTS.md`, `CLAUDE.md`, or
your agent's equivalent):

```markdown
## Skills
- Before writing or changing Django code, consult the `django-development` skill, and the
  `celery` skill for task definitions and call sites.
- Rules in this file and in project skills override both.
- Use `django-code-review` for any code review request.
```

This turns "the agent might notice" into a standing instruction. It's also the natural place to
start your project layer: the precedence model gives rules here priority over the recipes.

### Invoke a skill explicitly

When it matters, don't rely on matching. Name the skill:

> "Use the django-development skill while you write this view."

In Claude Code, skills can also be run directly as slash commands, e.g. `/django-code-review`.

### Check that a skill was used

Claude Code shows each skill as it loads, in the session transcript. If a skill you expected
doesn't appear, it wasn't used. With other agents, ask which skills they consulted.

### When a skill doesn't trigger

In order of effort:

1. Add the pointer above to your instructions file.
2. Invoke the skill by name for the task at hand.
3. Edit the `description` in your local copy of the skill's `SKILL.md`. Agents choose skills by
   matching the description, so mention the work your team actually does (e.g. "DRF serializers",
   "htmx views"). These are recipes, so adapting your copy is expected.

---

## Contributing

Contributions are welcome, within scope: Django idioms, review playbooks, and project-scaffold
improvements. There is no fixed template; see any existing skill for the shape to follow —
`SKILL.md` + `README.md`, and `references/` for a playbook-based skill like
`django-code-review`. No scripts or tests required for a recipe.

Open a pull request with your skill in its own top-level directory. Add a row to the table in
this README so it shows up in the index.
