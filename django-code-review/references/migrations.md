# Migrations Playbook

Apply whenever `models.py` or `migrations/` files are changed. Rule shape follows
`django-development`: **Do/Don't**, **Why**, **Except**, **Applies** (version-specific rules
only), **Evidence**.

---

## Model/migration consistency

### A migration's field parameters must match the model exactly `migrations/field-parameter-drift`
- **Do:** check that `null`, `blank`, `default`, and `max_length` in the migration match the
  model definition exactly.
- **Why:** Django generates migrations from the model state at the time `makemigrations` ran;
  a model edited by hand afterwards (or a migration edited by hand) can silently drift from what
  the model file now says, so the database schema stops matching what the ORM believes it is.
- **Evidence:** Django migration docs — migrations are a snapshot of model state, not a live
  reflection of the model file.

### Deliberately choose `on_delete`, don't leave it as the first thing that worked `migrations/on-delete-choice`
- **Do:** check that `CASCADE`, `SET_NULL`, or `PROTECT` was a deliberate choice for each
  foreign key, not a default left over from scaffolding.
- **Why:** `on_delete` determines what happens to related rows when the referenced row is
  deleted — `CASCADE` propagates deletes an author may not expect; `PROTECT` blocks a delete the
  caller may expect to succeed.
- **Evidence:** see `django-development`'s `models/cascade-audit` for the specific cascade-delete
  failure mode this guards against.

### Flag `unique_together`/`index_together`; require `UniqueConstraint`/`Index` instead `migrations/deprecated-meta-options`
- **Don't:** add new `unique_together` or `index_together` entries.
- **Why:** both are deprecated in favour of `Meta.constraints` (`UniqueConstraint`) and
  `Meta.indexes` (`Index`), which support more expressive conditions (`condition=`, functional
  indexes) that the tuple-based options never did.
- **Evidence:** Django deprecation notes for `unique_together`/`index_together`.

### A single-column unique foreign key should be a `OneToOneField` `migrations/fk-unique-should-be-onetoone`
- **Do:** flag `ForeignKey(unique=True)` and suggest `OneToOneField` instead.
- **Why:** `OneToOneField` is semantically explicit about the 1:1 relationship and gets the
  matching reverse-accessor behaviour (a single related object, not a manager) for free.
- **Evidence:** Django docs, `OneToOneField` — "conceptually equivalent to a `ForeignKey` with
  `unique=True`", provided for exactly this case.

---

## Blue-green deployment locking risks

In a blue-green deployment, old and new application code run simultaneously against the same
database during the switchover window. Migrations run before the new code is activated, so the
database must be compatible with *both* versions at once, and a lock held too long blocks the
app entirely for its duration.

### A new `NOT NULL` column needs a database-level default, not just `null=True` later `migrations/add-column-locking`
- **Do:** add a `NOT NULL` column either as `null=True` first (backfill, then constrain in a
  later migration) or with a database-level default (`db_default=`, Django 5.0+).
- **Why:** PostgreSQL takes an `ACCESS EXCLUSIVE` lock — blocking all reads and writes — for the
  full duration of adding a `NOT NULL` column with no database-level default. Django's
  `default=` argument is Python-side only and does not prevent this lock.
- **Applies:** `db_default=` requires Django >= 5.0.
- **Evidence:** PostgreSQL `ALTER TABLE` documentation on `ADD COLUMN` rewrite behaviour.

### Renaming or changing the type of a column needs a multi-phase migration `migrations/rename-retype-column`
- **Don't:** rename a column or table, or change a column's underlying database type, in a
  single migration during blue-green deployment.
- **Why:** the old code references the old name/type; the new code references the new one. A
  single-step rename or retype breaks whichever version is still running against it, and a type
  change additionally takes an `ACCESS EXCLUSIVE` lock if the types are incompatible.
- **Do:** use a three-phase approach for renames (add the new name, dual-write, retire the old
  name); flag any `AlterField` that changes the underlying column type for the same reason.
- **Evidence:** standard blue-green/expand-contract migration pattern.

### An index change on a large table needs the concurrent variant and `atomic = False` `migrations/index-change-locking`
- **Do:** for `AddIndex`/`RemoveIndex` on large tables, use `AddIndexConcurrently`/
  `RemoveIndexConcurrently` (`django.contrib.postgres.operations`) or `RunSQL` with
  `CREATE`/`DROP INDEX CONCURRENTLY` and a matching reverse operation. Set `atomic = False` on
  the Migration class either way.
- **Why:** Django's plain `AddIndex`/`RemoveIndex` do not use `CONCURRENTLY`, so they take an
  `ACCESS EXCLUSIVE` lock for the operation's full duration — and `CONCURRENTLY` cannot run
  inside the transaction Django normally wraps a migration in, hence `atomic = False`.
- **Evidence:** PostgreSQL `CREATE INDEX CONCURRENTLY` documentation; Django migration
  `atomic` attribute docs.

### A new unique constraint, PK, FK, or check constraint needs `NOT VALID` + a separate validate step `migrations/constraint-validation-locking`
- **Do:** for a new `UNIQUE` constraint, primary key, foreign key constraint, or
  `CheckConstraint` on an existing table, add it `NOT VALID` via `RunSQL`, then `VALIDATE
  CONSTRAINT` in a following step (for a foreign key, also add the column itself with
  `db_constraint=False` first, backfill, then add the constraint).
- **Why:** adding any of these the plain way validates every existing row under a table lock —
  `SHARE ROW EXCLUSIVE` for foreign keys, a full table lock for unique constraints/primary keys —
  blocking writes for the whole scan. `NOT VALID` skips the scan at add-time; `VALIDATE
  CONSTRAINT` takes a much weaker lock and can run separately.
- **Evidence:** PostgreSQL `ALTER TABLE ... ADD CONSTRAINT ... NOT VALID` documentation.

### Adding a database-enum value must set `atomic = False` `migrations/enum-value-non-transactional`
- **Do:** set `atomic = False` on the Migration class for any migration that adds a new
  `TextChoices`/`IntegerChoices` value backed by a PostgreSQL enum type.
- **Why:** `ALTER TYPE ... ADD VALUE` cannot run inside a transaction; Django wraps migrations in
  a transaction by default, so the migration fails unless atomicity is explicitly disabled.
- **Evidence:** PostgreSQL docs, `ALTER TYPE ... ADD VALUE` — "cannot be executed inside a
  transaction block."

### DDL in `RunSQL` should set a lock timeout `migrations/runsql-lock-timeout`
- **Do:** prefix hand-written DDL in `RunSQL` with `SET lock_timeout = '5s';` (or similar).
- **Why:** without a timeout, DDL that needs a lock queues behind any long-running query holding
  a conflicting lock, then holds its own lock for its full duration once acquired — blocking
  every subsequent read and write in the meantime. A timeout fails fast instead.
- **Evidence:** PostgreSQL `lock_timeout` configuration parameter documentation.

---

## Backwards compatibility with running code

### A new `NOT NULL` column breaks old-code inserts until it has a server-side default `migrations/not-null-breaks-old-inserts`
- **Do:** give a new `NOT NULL` column a database-level default (`db_default=`, Django 5.0+) or
  make it nullable initially.
- **Why:** old application code doesn't know to supply the new column on `INSERT`. Without a
  database-level default, every insert from the still-running old code fails the moment the
  migration completes — before the new code is even deployed.
- **Applies:** `db_default=` requires Django >= 5.0.
- **Evidence:** reproduces the same mechanism as `migrations/add-column-locking`, from the
  compatibility angle rather than the locking angle.

### Backfill before removing `null=True` `migrations/backfill-before-not-null`
- **Do:** backfill every `NULL` value in a prior data migration before an `AlterField` removes
  `null=True`.
- **Why:** the constraint-adding migration fails outright at migration time if any row still
  contains `NULL`.
- **Evidence:** PostgreSQL `ALTER TABLE ... SET NOT NULL` validates existing rows.

### Remove a field from all ORM usage and deploy before dropping its column `migrations/field-removal-sequencing`
- **Do:** ensure a field being dropped is removed from every `models.py`/queryset reference and
  that code is deployed *before* the column-dropping migration runs. The same applies to
  dropping a model/table entirely.
- **Why:** the still-running old code raises `ProgrammingError` (or fails entirely, for a
  dropped table) on any query that selects or filters on a column/table that no longer exists.
- **Evidence:** reproduces the blue-green "old code, new schema" incompatibility window directly.

### A new `NOT NULL` foreign key needs the same nullable-first treatment `migrations/new-fk-not-null`
- **Do:** make a new foreign key nullable initially if the old code's inserts won't supply it.
- **Why:** same mechanism as any other new `NOT NULL` column — old-code inserts omit it and fail.
- **Evidence:** see `migrations/not-null-breaks-old-inserts`.

### Narrowing `max_length` can fail on existing data `migrations/narrowing-max-length`
- **Do:** check whether any existing value exceeds a new, smaller `max_length` before narrowing
  it.
- **Why:** Django doesn't retroactively validate existing rows against a narrowed `max_length` —
  the column accepts the narrower value going forward, but any `UPDATE` touching an
  already-too-long existing row then fails at the database level if a length check constraint
  exists, or silently stores a value Django itself would reject on next save.
- **Evidence:** general schema-narrowing data-compatibility concern.

---

## Data migrations

### A data migration over a large table must be batched `migrations/data-migration-batching`
- **Do:** use `.iterator(chunk_size=1000)` (or similar explicit pagination) with
  `bulk_update()`/`bulk_create()`, rather than loading `.all()` or an unchunked queryset into a
  single `RunPython` pass.
- **Why:** migrating millions of rows in one transaction holds locks (and memory) for the
  transaction's entire duration, which can be minutes or hours on a large table — unacceptable
  for a migration that's supposed to run as part of a deploy.
- **Evidence:** Django `QuerySet.iterator()` docs on `chunk_size` and reduced memory use for
  large querysets.

### A data migration should tolerate being re-run or resumed `migrations/data-migration-resumability`
- **Do:** write `RunPython` data migrations so a partial failure can be safely re-run — e.g. by
  making the operation idempotent, or tracking progress so a resume doesn't redo completed work.
- **Why:** a migration that fails partway through a large batch, with no way to safely resume,
  turns an ordinary deploy failure into a data-consistency incident.
- **Except:** a data migration guaranteed to run inside a single short transaction (small table,
  fast operation) doesn't need this treatment — the whole thing either commits or rolls back.
- **Evidence:** general operational-safety concern for long-running, multi-step operations.

### A data migration must not assume every existing row matches today's shape `migrations/data-migration-shape-assumptions`
- **Do:** check whether the data migration's logic holds for rows written under a previous
  schema version — a field that's `NOT NULL` today may have had `NULL` rows historically; an
  enum value referenced by old rows may have since been retired.
- **Why:** a migration written against "the shape the model has now" silently mishandles or
  crashes on rows that predate that shape, since nothing re-validates historical data against
  the current model definition.
- **Evidence:** general schema-evolution concern — migrations run once, against whatever data
  actually exists, not against an idealized dataset.

### Guard `RunSQL` `CREATE`/`DROP` with existence checks `migrations/runsql-existence-guards`
- **Do:** use `IF NOT EXISTS` / `IF EXISTS` on `CREATE`/`DROP` statements inside `RunSQL`.
- **Why:** without the guard, re-running the migration (e.g. after a partial failure, or in an
  environment where the object was created out-of-band) raises an error instead of being a safe
  no-op.
- **Evidence:** standard idempotent-DDL practice.

---

## Dependency ordering

### A migration must declare every migration it actually depends on `migrations/missing-dependency`
- **Do:** check that `dependencies` lists every migration that must have already run — including
  a cross-app dependency introduced by `SeparateDatabaseAndState` or a foreign key to a model in
  another app.
- **Why:** a missing dependency means Django's migration graph doesn't guarantee this migration
  runs after the one that creates a table or column it needs — it can run before, and fail.
- **Evidence:** Django migration dependency graph docs.

---

## Migration history integrity

### Flag more than one leaf migration in an app `migrations/diverged-leaf-migrations`
- **Do:** check whether an app has more than one leaf migration (two migrations with no shared
  successor).
- **Why:** this indicates the migration history diverged — usually two branches each added
  migrations independently — and needs a merge migration (`makemigrations --merge`) before it
  can be deployed cleanly.
- **Evidence:** Django's own `makemigrations --merge` mechanism exists specifically to resolve
  this state.

### Migration names should say what they do `migrations/non-descriptive-names`
- **Do:** flag an auto-generated name like `0042_auto_20240101` with no indication of purpose.
- **Why:** `showmigrations` and `git log` both become much harder to navigate when names don't
  describe their content, especially when diagnosing which migration introduced a problem.
- **Evidence:** general maintainability concern, not a Django-enforced rule.

---

## Rollback safety

### A `RunPython` migration needs a `reverse_code` function `migrations/irreversible-runpython`
- **Do:** provide `reverse_code` for any `RunPython` operation, unless it's genuinely
  impossible to reverse (and that's stated explicitly, not just omitted).
- **Why:** an irreversible migration blocks `migrate` from rolling back past it during an
  incident, forcing a forward-fix instead of a rollback at exactly the moment a rollback was
  needed.
- **Except:** some operations are genuinely one-way (e.g. deleting data that can't be
  reconstructed) — in that case, the lack of `reverse_code` should be a deliberate, documented
  choice, not an oversight.
- **Evidence:** Django `RunPython` docs on `reverse_code`.

### A reverse migration must leave the database compatible with the previous app version `migrations/reverse-migration-consistency`
- **Do:** check that rolling back the migration leaves the schema in a state the previous
  application version can actually operate against — not just "the forward migration undone."
- **Why:** a naive reverse (e.g. dropping a column the old code never wrote to, but a newer
  version does expect) can leave the database in a state neither app version handles correctly.
- **Evidence:** same blue-green compatibility reasoning as the forward-migration rules above,
  applied to the rollback path.
