# Celery Tasks Playbook

Apply whenever task definitions or `.delay()`/`.apply_async()` calls are added or changed. Rule
shape follows `django-development`: **Do/Don't**, **Why**, **Except**, **Evidence**. For the
underlying task-argument and concurrency rules, see the `celery` skill — this playbook applies
them as review checks.

---

### Check that a task is safe to run twice `celery/idempotency`
- **Do:** check what happens if the task runs twice for the same logical unit of work (e.g.
  after a broker redelivery or a manual retry).
- **Why:** Celery's default delivery guarantees allow a task to be delivered more than once;
  a task that isn't idempotent can duplicate its side effects (double-charge, double-send,
  double-create) on redelivery.
- **Except:** a task whose side effect is itself naturally idempotent (e.g. `set`-style updates
  to a fixed value) doesn't need extra guarding.
- **Evidence:** see the `celery` skill's `celery/pass-pks` rule and its Celery user-guide
  citation on task state and retries.

### Check that model arguments are primary keys, not instances `celery/pks-not-instances`
- **Do:** check that `.delay()`/`.apply_async()` calls pass `obj.pk`, not `obj` itself.
- **Why:** this is the `celery` skill's `celery/pass-pks` rule, applied at review time — passing
  an instance either fails serialization or arrives as a stale snapshot.
- **Evidence:** `celery` skill, `celery/pass-pks`.

### Check for stale-data risk in a delayed task `celery/stale-data-risk`
- **Do:** check whether the task re-fetches current state (rather than trusting data captured at
  `.delay()` time) for anything that could have changed between enqueue and execution.
- **Why:** a task can sit in the queue for an arbitrary amount of time before a worker picks it
  up — any assumption baked in at enqueue time about the state of the world is a race condition
  against whatever changes in the meantime.
- **Evidence:** see `django-development`'s `models/integrityerror-not-precheck`, which covers the
  same race-condition shape for concurrent writes.

### Check that task exceptions aren't silently swallowed `celery/exception-handling`
- **Do:** check that a broad `try/except` inside a task doesn't catch and discard an exception
  that should instead fail the task (so retry/alerting machinery sees it).
- **Why:** a task that swallows its own failures looks successful in monitoring while silently
  not doing its job — the failure becomes invisible instead of actionable.
- **Except:** a deliberately-expected, specific exception that the task has a defined fallback
  for is fine to catch narrowly — the concern is broad catches that hide unexpected failures.
- **Evidence:** general task-reliability concern; Celery's retry/alerting tooling only works on
  exceptions that actually propagate.

### Check whether a task can trigger a cascade of further tasks `celery/cascade-and-queue-flooding`
- **Do:** check whether this task enqueueing further tasks (directly, or via a signal handler
  it triggers) is bounded, and won't flood the queue under a large enough input.
- **Why:** an unbounded fan-out (e.g. one task per row of an unexpectedly large queryset) can
  overwhelm the queue and starve other work, especially if each enqueued task can itself fan out
  further.
- **Evidence:** general queue-capacity concern; see `references/performance.md` for the same
  check applied to any hot-path code, not just tasks.
