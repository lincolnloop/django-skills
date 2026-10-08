# Signals Playbook

Apply whenever signal definitions or handlers are added or changed. Rule shape follows
`django-development`: **Do/Don't**, **Why**, **Except**, **Evidence**.

---

### A signal handler must guard against a `None` instance or sender `signals/none-guard`
- **Do:** check that the handler doesn't assume `instance`/`sender` (or a field on `instance`)
  is always populated.
- **Why:** signals fire from code paths the handler's author doesn't control — a bulk operation,
  a fixture load, or a partially-constructed instance mid-`__init__` can all send a signal with
  less data than the handler expects.
- **Evidence:** Django signal docs — handlers receive whatever the sender actually provides, with
  no guarantee beyond the documented signal arguments.

### Connect signals in `AppConfig.ready()`, not at module level `signals/connect-in-ready`
- **Do:** check that `@receiver`/`signal.connect()` calls run from `AppConfig.ready()` (directly
  or via an imported `signals` module), not at import time of an arbitrary module.
- **Why:** `ready()` is the one place Django guarantees runs exactly once per process, after the
  app registry is fully populated — connecting elsewhere risks double-connection on reload, or
  connecting before the models it references are ready.
- **Evidence:** Django docs, "Applications" — `AppConfig.ready()`.

### Flag a handler doing heavy synchronous work `signals/heavy-work-in-handler`
- **Do:** check whether the handler does a network call or heavy DB work synchronously, and
  whether it should hand off to a Celery task instead.
- **Why:** a signal handler runs inline, inside whatever request or transaction triggered it —
  slow synchronous work there adds that latency to every caller, with no way to retry
  independently if it fails.
- **Except:** work that must complete before the triggering transaction commits (e.g. a
  same-transaction integrity check) can't be deferred to a task without changing its guarantees.
- **Evidence:** see the `celery` skill's `celery/pass-pks` rule for the task-boundary half of
  this handoff.

### A handler must be safe to run twice on the same object `signals/idempotency`
- **Do:** check whether the handler can run twice for the same object (e.g. a `post_save` firing
  again from an unrelated `save()` call) without duplicating side effects.
- **Why:** Django doesn't guarantee a signal fires exactly once per logical event — a `save()`
  anywhere in the call chain re-fires `post_save`, and retried tasks or request retries can
  re-trigger the same signal.
- **Evidence:** Django signal docs don't promise exactly-once delivery; it's a property the
  handler itself must provide.

### Use `created` to distinguish insert from update in `post_save` `signals/created-kwarg`
- **Do:** check that a `post_save` handler that behaves differently for a new vs. existing
  object branches on the `created` kwarg, rather than inferring it some other way (e.g. checking
  whether a field is empty).
- **Why:** `created` is the signal's own authoritative answer to "was this an INSERT or an
  UPDATE" — any other inference is an approximation that can be wrong for edge cases the
  approximation didn't anticipate.
- **Evidence:** Django docs, `post_save` signal — `created` argument.

### Check whether a signal's side effects are bounded `signals/side-effect-chains`
- **Do:** check whether saving one object can trigger a chain of further saves on other objects
  (via this handler, or an interaction with other signals/middleware/hooks), and whether that
  chain is intentional and bounded.
- **Why:** an unbounded or unexpected save chain can cause duplicate work, race conditions
  between the links in the chain, or — in the worst case — infinite recursion if two handlers
  each re-trigger the other.
- **Evidence:** general signal-composition risk; Django's signal dispatch has no built-in
  recursion guard.
