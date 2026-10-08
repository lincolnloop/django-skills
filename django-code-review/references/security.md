# Security Playbook

Apply whenever views, forms, queries, or file-handling code is added or changed. Rule shape
follows `django-development`: **Do/Don't**, **Why**, **Except**, **Evidence**.

---

### Sanitise user input before it reaches a query, shell command, file path, or template `security/input-sanitisation`
- **Do:** check that user-supplied values are validated or escaped before being used to build a
  query, a shell command, a file path, or rendered into a template in a context that disables
  autoescaping.
- **Why:** each of these is a distinct injection surface (SQL, OS command, path traversal, XSS)
  with its own escaping rules — assuming "Django escapes everything" skips the cases where it
  explicitly doesn't (raw SQL, `subprocess`, `|safe`/`mark_safe`).
- **Evidence:** Django security docs, "Security in Django" overview.

### Flag raw queries, `.extra()`, and string-interpolated filters for SQL injection `security/sql-injection`
- **Do:** check any `.raw()`, `.extra()`, or manually-built query string for unescaped user
  input, same as `references/querysets.md`'s `querysets/raw-sql-injection-risk`.
- **Why:** these bypass the ORM's parameterized-query escaping.
- **Evidence:** Django docs, "Performing raw SQL queries" — explicit warning on parameters vs.
  string interpolation.

### Sensitive data must not be logged, stored in plain text, or appear in a URL `security/sensitive-data-exposure`
- **Do:** check that API keys, tokens, passwords, and PII aren't passed to a logger, written to
  an unencrypted field, or included in a URL (query string or path).
- **Why:** log aggregators, URL histories, and referrer headers all persist or forward this data
  far outside the code's own control, often to third parties, long after the request completes.
- **Evidence:** OWASP "Sensitive Data Exposure" guidance.

### Validate file upload paths against traversal `security/file-upload-path-validation`
- **Do:** check that a file upload's destination path is constructed from a validated/sanitised
  filename, not used directly from user input.
- **Why:** an unvalidated filename containing `../` segments can write outside the intended
  upload directory.
- **Evidence:** OWASP "Path Traversal" guidance; Django's `FileField`/`ImageField` handle this
  for standard uploads, but custom file-handling code (e.g. a management command processing an
  uploaded archive) must do it itself.

### Every view that requires permission must actually check it `security/missing-permission-check`
- **Do:** check that `login_required`, `permission_required`, or an equivalent `has_permission`
  check is present on every view that should require it — including a new view added alongside
  existing protected ones, which can be forgotten precisely because the pattern "looks covered"
  elsewhere in the same file.
- **Why:** a view with no permission check is reachable by anyone who can guess or discover its
  URL, regardless of what the UI does to hide the link to it.
- **Evidence:** Django docs, "The Django Admin" and "View decorators" — `login_required`/
  `permission_required` are opt-in per view, not inherited automatically.

### Check whether a new endpoint exposes data it shouldn't `security/endpoint-data-exposure`
- **Do:** check that a new endpoint's response doesn't include fields (via a serializer, a
  template, or a queryset `values()`) that the requesting user shouldn't see.
- **Why:** a serializer or template built by copying an existing one can carry over fields
  (internal notes, other users' data, soft-deleted records) that were fine for their original
  audience but not for this endpoint's.
- **Evidence:** general least-privilege data-exposure concern.
