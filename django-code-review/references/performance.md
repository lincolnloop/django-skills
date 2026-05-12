# Performance and Scalability Playbook

Apply whenever querysets, bulk operations, or hot-path code is added or changed.

- Will the change perform acceptably on production data volumes? Consider table sizes and query
  plans.
- Are there missing database indexes for new filter/sort fields?
- Does the code load entire querysets into memory where pagination or iteration would be safer?
- Are external API calls (OpenAI, Wikipedia, etc.) inside a hot code path? Are they rate-limited
  or cached appropriately?
- Could a new Celery task trigger a cascade of further tasks? Is there a risk of queue flooding?
