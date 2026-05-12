# Correctness Playbook

Apply to every code change.

## Logic and control flow

- Does the code do what the description says it does?
- Are there logic errors, off-by-one errors, incorrect comparisons, or wrong variable references?
- Does conditional logic cover all branches? Are there implicit assumptions that could fail
  silently?
- Are return values used correctly? Can a function return `None` where a value is expected?

## Edge cases

Consider: empty inputs, `None` values, empty querysets, zero counts, very large inputs,
concurrent writes.

## Data mutations

For deletes, updates, and bulk operations: could the query match more rows than intended?
Is there a missing filter?

## Paired operations

Where code performs one half of a paired operation (build/query, read/write, encode/decode,
serialize/deserialize, encrypt/decrypt), check that any explicit configuration on one side is
matched explicitly on the other. Relying on an implicit database, runtime, or library default on
one side while the other is explicit creates environment-dependent behaviour that works locally
but silently fails wherever the default differs.

Specific things to look for:

- One side specifies a locale, encoding, collation, or text search config; the other omits it.
- One side specifies a cipher, hash algorithm, or serialization format; the other uses a library
  default.
- One side is in application code; the other is in a management command, migration, or Celery
  task — places where implicit defaults may differ between environments.
