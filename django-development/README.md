# Django Development Recipe

A recipe of general Django idioms: how the framework actually behaves and how to use it,
independent of any one project. Each rule is stated as a **Do/Don't**, a **Why** (citing Django
source or docs), and an **Except** where it stops applying, organised by the layer you're
writing — models, views, templates, tests.

> **This is a recipe, not a tool.** It works as-is, but its value grows when you layer your own
> project's conventions on top. The skill itself documents a precedence model: project
> conventions and package-specific skills (e.g. a `celery` skill) override what's here. Treat
> this as the baseline layer, not the last word.

## What it covers

| Layer | Rules |
|---|---|
| Models and the ORM | Cascade deletion audits, constraint-backed uniqueness, model instances vs. dicts |
| Views and template context | What context processors already add, and when they don't run |
| Templates and template tags | Per-template `{% load %}`, filter-argument lookup failures, presentation in model properties, removed builtins |
| Tests | Exercising the branch a fix enables, destructive round-trip coverage |

## Installation

```bash
npx skills add lincoln-loop/django-skills --skill django-development
```

Or globally:

```bash
npx skills add lincoln-loop/django-skills --skill django-development --global
```

## Using it

This is a **background** skill: nobody asks for it by name, so the agent has to match the code
it's writing against the skill's description. To make that dependable, add the pointer from the
[root README](../README.md#make-background-skills-dependable) to your project's `AGENTS.md` or
`CLAUDE.md`.

Prompts where it should apply:

> "Add a list view for published articles, with the author's name on each row."
>
> "Move the article card into its own include so the sidebar can reuse it."
>
> "Write a management command that clears and reloads the categories table."

Each touches a rule here, respectively:
- handing model instances to the template and not re-adding what the context already provides;
- re-declaring `{% load %}` in an extracted include;
- auditing cascades before a bulk clear. To be certain the skill is used, name it:

> "Use django-development while you write the article list view."

If it isn't being picked up, see
[When a skill doesn't trigger](../README.md#when-a-skill-doesnt-trigger).

## Adapting for your project

- **Add a project layer.** Create your own `project-conventions` skill (or an `AGENTS.md`) for
  choices specific to your codebase — this skill explicitly defers to it.
- **Add package layers.** If you use Celery, DRF, or another library with its own idioms, add a
  skill for it; this recipe's precedence rules already expect one.
- **Version-specific rules.** A few rules only apply above a given Django version (see the
  **Applies:** field). Check your pinned Django version before assuming one holds.
- **Extend, don't just trim.** As you hit new framework gotchas, add rules in the same
  Do/Why/Except shape so they stay consistent with the rest of the skill.

## Prerequisites

- Node.js ≥ 18 (for the `npx skills` CLI)
