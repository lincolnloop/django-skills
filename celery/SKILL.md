---
name: celery
description: Consult before or while writing Celery task definitions or call sites (`@shared_task`, `.delay()`, `.apply_async()`) in a Django project. General Celery idioms, not project-specific. Package layer of the skill hierarchy; overrides django-development, and is overridden by project-conventions.
version: 0.1.0
---

# Celery

How to use Celery well with Django, independent of any one project. Rule shape, version tags
and precedence follow `django-development` (see its "Precedence" and "Rule shape" sections).
This skill sits above it and below `project-conventions`.

## Task arguments

### Pass primary keys, not model instances, to tasks `celery/pass-pks`
- **Do:** call `task.delay(obj.pk)` and re-fetch inside the task. Handle `DoesNotExist`,
  since the row may have been deleted before the worker runs.
- **Why:** arguments are serialised. An instance is either rejected (JSON serialiser) or arrives
  as a snapshot that can be stale by the time the task runs. That's a race condition, not just
  wasted bandwidth.
- **Overrides:** `django-development` › `models/instances-as-data-carriers`. A task queue is a
  process boundary.
- **Evidence:** Celery user guide, "Tasks › State": model objects "shouldn't be passed on as
  arguments to tasks … it's almost always better to re-fetch the object from the database when
  the task is running".

## Concurrency

The `django-development` rule `models/integrityerror-not-precheck` applies directly to task code:
tasks run concurrently by design.
