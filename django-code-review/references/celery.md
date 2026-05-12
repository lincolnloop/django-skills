# Celery Tasks Playbook

Apply whenever task definitions or `.delay()` / `.apply_async()` calls are added or changed.

- Is the task idempotent? What happens if it runs twice?
- Are model instances passed by primary key, not as objects?
- Is there a risk of the task operating on stale data if it is delayed?
- Does the task handle exceptions appropriately and not silently swallow errors?
- Could a new task trigger a cascade of further tasks? Is there a risk of queue flooding?
