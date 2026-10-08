---
name: django-development
description: Consult before or while writing Django code — views, templates and template tags, models and querysets, forms, admin, signals, management commands, tests. General Django idioms (not project-specific), organised by the layer being written, each stated as a rule to apply while generating code. Lowest layer of the skill hierarchy; package skills and project-conventions override it.
version: 0.2.0
---

# Django Development

General Django idioms: how the framework works and how to use it, independent of any one project.
Find the section for the layer you are writing (the file you are in) and apply its rules.

## Precedence

Skills form a hierarchy. When rules conflict, the higher layer wins:

1. **Project:** your project's own conventions (e.g. an `AGENTS.md` or a `project-conventions` skill)
2. **Packages:** one skill per third-party library (e.g. `celery`)
3. **Django:** this skill

A rule in a higher layer that contradicts one here names it in an **Overrides:** line, so the
conflict is explicit. Before applying a rule from this skill, check that no higher layer
overrides it.

## Rule shape

Every rule uses the same fields, so developers and agents can read it at a glance:

- **Do / Don't:** the action, in one line
- **Why:** the mechanism, citing Django source or docs where possible
- **Except:** where the rule stops applying
- **Applies:** Django versions, only when the rule is version-specific
- **Evidence:** what grounds it (a PR, an incident, a source reference)

**Version-specific rules.** A rule with no **Applies:** line holds for every supported Django
version. A rule with one (e.g. `Django >= 5.1`) only applies when the project's Django version
matches. Read the version from the pinned dependency (`requirements/*.txt`, `uv.lock`, or
`pyproject.toml`) rather than assuming one.

---

## Models and the ORM

### Before a bulk clear, enumerate every cascade into the cleared models `models/cascade-audit`
- **Do:** before `Model.objects.all().delete()` (or `_base_manager`), list every
  `on_delete=CASCADE` foreign key that points at the model, including relations the code does
  not manage.
- **Why:** Django emulates cascades in Python and follows every relation, whatever the calling
  command thinks it owns.
- **Evidence:** Django's deletion collector (`django.db.models.deletion.Collector`) walks every
  `on_delete=CASCADE` relation pointing at the model, not just the ones a particular command is
  aware of — clearing all `Author` rows also cascades through a `Book.author` CASCADE FK and
  silently removes every `Book`, even from an app the calling code never imports.

### Enforce uniqueness with the constraint, not a pre-check `models/integrityerror-not-precheck`
- **Do:** in code that can run concurrently (task workers, importers), back uniqueness with a
  database constraint, catch `IntegrityError` and retry, rather than check-then-write.
- **Why:** the existence check isn't atomic with the write, so two workers can both pass it.
- **Evidence:** a classic check-then-act race: two concurrent requests can both pass
  `Model.objects.filter(slug=slug).exists()` before either has written, producing duplicate
  slugs even though a `UniqueConstraint` would have caught it. Django's own `validate_unique()`
  documentation acknowledges this isn't safe under concurrent writes without a DB-level
  constraint.

### Hand model instances to templates, not dicts built from them `models/instances-as-data-carriers`
- **Do:** pass model instances (or querysets) to templates and between functions in the same
  process. Put derived values on the model (`@property`, `@cached_property`), not in the view.
- **Why:** instances keep relationship traversal, `get_absolute_url`, display methods and
  `select_related` data available. Flattening into dicts duplicates the model in a weaker form.
- **Except:** values that cross a process boundary (task queues, caches, JSON responses) need
  primitives; see the `celery` skill. Use `values()`/`values_list()` deliberately for large
  read-only exports where instance overhead matters.
- **Evidence:** Django design philosophy ("Include all relevant domain logic" in the model).

## Views and template context

### Don't put `request`, `view`, `user`, `perms` or `messages` into the context `views/implicit-context`
- **Don't:** add these to a context dict, e.g. `context['request'] = request`.
- **Why:** class-based views add `view` in `ContextMixin.get_context_data`
  (`kwargs.setdefault('view', self)`). Context processors add `request`
  (`context_processors.request`), `user` and `perms` (`auth`) and `messages`
  (`messages`) whenever the template is rendered with a `RequestContext`: `render()`,
  `TemplateResponse`, and generic views. Check `TEMPLATES['OPTIONS']['context_processors']`
  for which ones are configured.
- **Except:** context processors **don't** run when:
  - rendering an inclusion tag's template (`RequestContext.new()` deliberately drops
    processor values, so use `takes_context=True` and pass on what the template needs);
  - calling `render_to_string()` without `request=`;
  - rendering outside a request (email, task workers, management commands).

  Function-based views get no `view` variable.
- **Evidence:** Django 5.1 source (`views/generic/base.py`, `template/context.py`).

## Templates and template tags

### Re-declare `{% load %}` in every template that uses a tag library `templates/load-per-file`
- **Do:** when extracting markup into an `{% include %}` file, give it its own `{% load %}`
  line for every library it uses.
- **Why:** tag libraries are per-template. An included template is parsed on its own, at the
  moment it is rendered, so it doesn't see the including template's loads.
- **Except:** libraries listed in `TEMPLATES['OPTIONS']['builtins']` are available everywhere.
- **Evidence:** the `TemplateSyntaxError` for a missing `{% load %}` only surfaces the first
  time that specific include is actually rendered — which can be long after code review and the
  test suite both pass, if the include path isn't exercised until then.

### A failed lookup in a filter *argument* raises `templates/filter-argument-lookups`
- **Don't:** rely on a filter argument rendering empty, e.g. `x|default:items.0.attr` when
  `items` may be empty.
- **Why:** `FilterExpression.resolve` catches `VariableDoesNotExist` for the main variable
  only. Each argument is resolved without that protection.
  - `{{ items.0.attr }}`, `{% with x=items.0.attr %}`, `{% if %}` and `{% for %}` all swallow
    the failure.
  - `|default:items.0.attr` raises it.
- **Do:** guard with `{% if items %}`, or resolve the value in the view.
- **Except:** indexed lookups in the main-variable position are safe; this concerns the
  argument position only.
- **Evidence:** `django/template/base.py` `FilterExpression.resolve()` — the try/except around
  `VariableDoesNotExist` wraps only the main variable's resolution, not its arguments.

### Prefer model properties and built-in filters for presentation `templates/presentation-in-properties-and-filters`
- **Do:** format values with model properties (`{{ book.full_title }}`) and built-in filters
  (`date`, `default`, `pluralize`, `truncatewords`), rather than building strings in the view.
- **Why:** this keeps views to fetching and routing, and keeps presentation where designers
  can see it.
- **Except:** anything that can fail at render time (a property that queries or raises, or a
  fallible filter argument, see `templates/filter-argument-lookups`) fails in front of the
  user. Projects that need polished error handling usually override this rule.
- **Evidence:** Django design philosophy (templates: "separate logic from presentation").

### Don't use template tags and filters removed from Django `templates/removed-builtins`
- **Don't:**
  - `{% ifequal %}`/`{% ifnotequal %}`: use `{% if a == b %}`.
  - `|length_is:n`: use `{% if value|length == n %}`.
- **Applies:**
  - `ifequal`/`ifnotequal` removed in Django >= 4.0.
  - `length_is` removed in Django >= 5.1.
- **Why:** these raise `TemplateSyntaxError` when parsed. Like a missing `{% load %}`, that
  only happens when something renders the template.
- **Evidence:** Django 4.0 release notes (`ifequal`/`ifnotequal` removal) and Django 5.1 release
  notes (`length_is` removal).

## Tests

### A fix's regression test must exercise the branch the fix enables `tests/exercise-enabled-branch`
- **Do:** when a fix makes a previously unreachable branch reachable (a guard, a fallback, an
  extracted include), test that branch, not only the one that reproduced the failure.
- **Why:** a test of the empty/absent case passes whether or not the enabled path works.
- **Evidence:** a regression test for a newly-enabled `{% include %}` that only asserts the
  disabled/absent case passes whether or not the enabled branch actually renders — the broken
  include can ship a second time under the same green test suite.

### Prove that a clear-and-reload round trip preserves what it restores `tests/destructive-round-trip`
- **Do:** for any destructive-then-restorative sequence (clear then reload), write a
  fixture-based test asserting that the specific restored data survives, not just that the
  command completes.
- **Why:** cascade and ordering bugs produce no error. They show up only as missing rows.
- **Evidence:** see `models/cascade-audit` — a clear-then-reload command can complete with no
  errors while a CASCADE relation outside the command's awareness silently drops rows it was
  supposed to restore.
