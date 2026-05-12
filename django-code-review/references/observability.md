# Error Handling and Observability Playbook

Apply whenever exception handling, logging, or task code is added or changed.

## Error handling

- Are exceptions caught at the right level of specificity? Bare `except:` or
  `except Exception:` that silently swallow errors should be flagged.
- Is there a risk of an unhandled exception leaving the system in an inconsistent state (e.g. a
  partially-written record, a locked queue item that is never unlocked)?

## Logging

- Are errors logged with enough context to diagnose them in production (object IDs, relevant
  field values)?
- Are new code paths covered by logging at an appropriate level (`DEBUG` for normal flow, `INFO`
  for significant events, `WARNING`/`ERROR` for problems)?

## Side effects

- Are the side effects of the change clearly bounded? Could saving one object trigger a chain of
  saves on others?
- Could the change cause a circular import? Check deferred imports inside functions.
- Does the change interact with any existing signals, middleware, or hooks in unexpected ways?
