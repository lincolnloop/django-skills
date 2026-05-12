# Signals Playbook

Apply whenever signal definitions or handlers are added or changed.

- Does the signal handler guard against being called with a `None` instance or sender?
- Are signals connected in `AppConfig.ready()`, not at module level?
- Does the handler do too much work synchronously (e.g. network calls, heavy DB work)? Should it
  defer to a Celery task?
- Is the handler idempotent? Could it run twice on the same object safely?
- Are `post_save` handlers using the `created` kwarg where appropriate to distinguish create vs
  update?
- Could saving one object trigger a chain of saves on others? Are the side effects clearly
  bounded?
- Does the change interact with any existing signals, middleware, or hooks in unexpected ways?
