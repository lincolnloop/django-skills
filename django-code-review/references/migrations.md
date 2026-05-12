# Migrations Playbook

Apply whenever `models.py` or `migrations/` files are changed.

---

## Model/migration consistency

- Does the migration match the model change exactly? Are field parameters (`null`, `blank`,
  `default`, `max_length`) consistent between the two?
- Are `on_delete` behaviours deliberate? (`CASCADE` vs `SET_NULL` vs `PROTECT`)
- Is `unique_together` or `index_together` used? Both are deprecated — new constraints must use
  `UniqueConstraint` and `Index` in `Meta.constraints` / `Meta.indexes`.
- Is `ForeignKey(unique=True)` used? It should be `OneToOneField`.

---

## Blue-green deployment safety

In a blue-green deployment, old and new application code run simultaneously against the same
database during the switchover window. Migrations run before the new code is activated, so the
database must be compatible with *both* versions at the same time.

### Locking risks

**Adding a column**
Safe if the column is `NULL`-able or has a `server_default`. Adding a `NOT NULL` column without
a database-level default takes an `ACCESS EXCLUSIVE` lock for the full duration on PostgreSQL,
blocking all reads and writes. The Django `default=` argument is Python-side only and does not
prevent the lock.
- Safe pattern: add as `null=True`, backfill, then add the `NOT NULL` constraint separately.

**Dropping a column**
The old code will fail immediately if it references a column that no longer exists. Remove the
column from all ORM references and deploy that first; the column drop comes in a later migration
after the old code is fully retired.

**Renaming a column or table**
Never safe in a single migration during blue-green. The old code uses the old name; the new code
uses the new name. Use a three-phase approach: add the new name, dual-write, retire the old name.

**Changing a column type**
Takes an `ACCESS EXCLUSIVE` lock and breaks the old code if the types are incompatible. Flag any
`AlterField` that changes the underlying database column type.

**Adding an index**
Django's `AddIndex` does **not** use `CONCURRENTLY` by default. For large tables, use
`AddIndexConcurrently` (from `django.contrib.postgres.operations`) or `RunSQL` with
`CREATE INDEX CONCURRENTLY` and a matching `DROP INDEX CONCURRENTLY` in the reverse. Either way,
the migration **must** set `atomic = False` at the class level.

**Removing an index**
`RemoveIndex` takes an `ACCESS EXCLUSIVE` lock on large tables. Use `RemoveIndexConcurrently`
or `RunSQL` with `DROP INDEX CONCURRENTLY`. Also requires `atomic = False`.

**Adding a `UNIQUE` constraint or primary key**
Always takes a full table lock. High-risk on large tables — should be preceded by a concurrent
unique index build; the constraint is then added referencing the existing index.

**Adding a foreign key constraint**
By default, acquires a `SHARE ROW EXCLUSIVE` lock and validates all existing rows. On large
tables this blocks writes for the full scan duration.
- Safe pattern: add the column with `db_constraint=False`, backfill, then add the constraint
  using a `NOT VALID` / `VALIDATE CONSTRAINT` two-step in `RunSQL`.

**Adding a `CheckConstraint`**
Like foreign keys, adding a check constraint validates all existing rows and holds a lock. Add it
with `NOT VALID` in `RunSQL`, then validate in a separate step.

**Adding a PostgreSQL enum value**
`ALTER TYPE ... ADD VALUE` cannot run inside a transaction. Any migration that adds a new
`TextChoices` / `IntegerChoices` value backed by a database enum must set `atomic = False` on
the Migration class.

**`RunSQL` DDL without a lock timeout**
A DDL statement in `RunSQL` that waits for a lock can queue behind a long-running query and then
hold that lock, blocking all subsequent reads and writes. Prefix DDL in `RunSQL` with
`SET lock_timeout = '5s';` to fail fast instead of blocking indefinitely.

---

## Backwards compatibility with running code

**New `NOT NULL` column without a default**
The old application code does not supply this column on `INSERT`, causing it to fail immediately
when the migration runs and before the new code is deployed. Always provide a database-level
`DEFAULT` or make the column nullable. Use `db_default=` (Django 5.0+) for a true server-side
default — Django's `default=` is Python-side only.

**Making a nullable column `NOT NULL` without backfilling**
An `AlterField` that removes `null=True` will fail at migration time if any rows contain `NULL`.
Backfill all `NULL` values in a prior data migration before applying the constraint.

**Dropping or renaming a field the old code reads**
The old application will raise `ProgrammingError` on any query that selects or filters on the
removed field. Ensure the field is removed from all ORM usage and deployed before the column is
dropped.

**Adding a new `NOT NULL` foreign key**
Inserts from the old code will fail because they do not supply the new field. Make it nullable
initially.

**Narrowing a `max_length`**
Existing values that exceed the new limit will cause errors on any subsequent `UPDATE` of those
rows.

**Deleting a model (dropping a table)**
The old code will fail on any access. The model must be removed from the codebase and deployed
before the table is dropped.

---

## Data migrations

- Does the data migration handle large tables efficiently? Migrating millions of rows in a single
  transaction holds locks for the entire duration. Use batched updates with explicit pagination.
- Does `RunPython` code call `.all()` or iterate the full queryset without chunking? Use
  `.iterator(chunk_size=1000)` and process in batches with `bulk_update()` / `bulk_create()`.
- Could the data migration fail partway through? Is it safe to re-run or resume?
- Does the data migration assume a data shape that may not hold for all existing rows (e.g.
  `NOT NULL` fields that were historically nullable, or retired enum values)?
- Does `RunSQL` use `CREATE` or `DROP` without `IF NOT EXISTS` / `IF EXISTS` guards?

---

## Dependency ordering

- Does the migration declare the correct `dependencies`? A missing dependency means it may run
  before a required table or column exists.
- If the migration touches a model owned by another app (via `SeparateDatabaseAndState` or a
  cross-app FK), is that app's migration listed as a dependency?

---

## Migration history integrity

- Does the app have more than one leaf migration (two migrations with no shared successor)?
  This indicates a diverged history — a merge migration is needed (`makemigrations --merge`).
- Are migration names descriptive? A name like `0042_auto_20240101` gives no indication of
  purpose in a `showmigrations` listing.

---

## Rollback safety

- Is the migration reversible? If `RunPython` is used, is a `reverse_code` function provided?
  An irreversible migration blocks rollback during an incident.
- If rolled back, will the reverse migration leave the database in a consistent state that the
  previous application version can operate against?
