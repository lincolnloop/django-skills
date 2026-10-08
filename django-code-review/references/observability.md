# Error Handling and Observability Playbook

Apply whenever exception handling, logging, or task code is added or changed. Rule shape follows
`django-development`: **Do/Don't**, **Why**, **Except**, **Evidence**.

---

### Catch exceptions at the right level of specificity `observability/bare-except`
- **Do:** flag a bare `except:` or broad `except Exception:` that silently swallows the error
  (no re-raise, no logging of the original exception) instead of handling a specific, expected
  exception type.
- **Why:** a broad silent catch hides failures the author didn't anticipate alongside the one
  they meant to handle — the code "works" in every case, including the ones where it's actually
  failing.
- **Except:** a broad catch that logs the full exception (traceback included) and then
  re-raises, or that sits at a genuine top-level boundary (e.g. a task's outermost wrapper that
  must not crash the worker), is a deliberate, different pattern from a silent swallow.
- **Evidence:** general exception-handling concern; Python's own guidance (PEP 8) discourages
  bare `except:` for the same reason.

### Check whether an unhandled exception can leave the system inconsistent `observability/inconsistent-state-on-failure`
- **Do:** check whether an exception partway through a multi-step operation (a partially-written
  record, a lock acquired but never released, a queue item claimed but never completed) leaves
  something in a state nothing else expects or can recover from.
- **Why:** the exception itself is usually visible (an error is logged, a task is marked
  failed) — the inconsistent state it leaves behind is often not, and surfaces later as a
  harder-to-diagnose symptom.
- **Evidence:** general transactional-safety concern; Django's `atomic()` context manager exists
  specifically to make multi-step DB writes all-or-nothing for this reason.

### Log errors with enough context to diagnose them without reproducing them `observability/logging-context`
- **Do:** check that error-path logging includes the relevant object IDs and field values needed
  to understand what happened, not just a generic message.
- **Why:** production logs are usually the only evidence available after the fact — a log line
  that says "failed to process" with no identifying information forces whoever investigates to
  reproduce the failure from scratch.
- **Evidence:** general observability concern.

### New code paths need logging at an appropriate level `observability/logging-level-appropriateness`
- **Do:** check that new code uses `DEBUG` for normal flow, `INFO` for significant events, and
  `WARNING`/`ERROR` for actual problems — not everything at one level.
- **Why:** logging everything at `INFO` (or `ERROR`) drowns out the signal that level is supposed
  to carry, making it harder to alert on or filter for the events that actually matter.
- **Evidence:** Python `logging` docs, log level guidance.

### Check whether side effects from this change are clearly bounded `observability/side-effect-boundaries`
- **Do:** check whether saving one object can trigger a chain of further saves (directly, or via
  signals/middleware/hooks this change interacts with), and whether a new deferred import inside
  a function hints at an existing circular-import problem being worked around.
- **Why:** an unbounded save chain risks duplicate work or races between its links; a deferred
  import inside a function body is often evidence of a circular dependency that will resurface
  the next time someone tries to import that module at the top level.
- **Evidence:** see `references/signals.md`'s `signals/side-effect-chains` for the same concern
  stated from the signal-authoring side.
