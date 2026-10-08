# Correctness Playbook

Apply to every code change. Rule shape follows `django-development`: **Do/Don't**, **Why**,
**Except**, **Evidence**.

---

### Check that every branch the change's description implies actually exists `correctness/branch-coverage`
- **Do:** verify logic and control flow match what the change claims to do — look for missing
  branches, off-by-one errors, incorrect comparisons, wrong variable references, and return
  values used as if they can't be `None` when they can.
- **Why:** a missing or wrong branch doesn't raise an exception — it silently does the wrong
  thing, so only a test (or review) that specifically exercises that branch catches it.
- **Evidence:** general defect-class — silent branch errors are one of the most common sources
  of undetected logic bugs precisely because nothing marks the failure.

### Treat empty, `None`, zero, and concurrent-write inputs as first-class cases `correctness/edge-cases`
- **Do:** for every new code path, consider empty inputs, `None` values, empty querysets, zero
  counts, very large inputs, and concurrent writes — not only the case the change was written to
  handle.
- **Why:** these are exactly the inputs most likely to differ between the author's manual
  testing and real traffic.
- **Evidence:** standard edge-case enumeration for defensive code review.

### A delete/update/bulk operation must filter to exactly the intended rows `correctness/bulk-op-scope`
- **Do:** for any `.delete()`, `.update()`, or other bulk operation, check that the filter
  clause matches only the rows the change intends to affect — no broader, no narrower.
- **Why:** an under-filtered queryset doesn't raise an error; it silently mutates or deletes more
  rows than intended, and the only symptom afterward is missing or wrong data.
- **Evidence:** see `django-development`'s `models/cascade-audit`, which covers the specific case
  of an `on_delete=CASCADE` relation widening a bulk delete's actual blast radius.

### Match implicit-vs-explicit configuration on both sides of a paired operation `correctness/paired-operations`
- **Do:** where code performs one half of a paired operation (build/query, read/write,
  encode/decode, serialize/deserialize, encrypt/decrypt), check that any explicit configuration
  on one side — locale, encoding, collation, text-search config, cipher, hash algorithm,
  serialization format — is matched explicitly on the other side too.
- **Why:** relying on an implicit database, runtime, or library default on one side while the
  other side is explicit creates environment-dependent behaviour: it works wherever the default
  happens to match, and silently breaks wherever it doesn't.
- **Except:** both sides can safely rely on the same default, as long as that default is
  verified identical in every environment the code runs in — don't assume it without checking.
- **Evidence:** PostgreSQL's full-text search config fallback is a concrete instance: a
  `tsvector` built with an explicit `config=` argument must be queried with the same explicit
  `config=`, or a search silently returns nothing in any environment whose
  `default_text_search_config` differs. See `references/querysets.md`.
