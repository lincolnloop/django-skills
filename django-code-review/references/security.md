# Security Playbook

Apply whenever views, forms, queries, or file-handling code is added or changed.

- Is user input sanitised before use in queries, shell commands, file paths, or templates?
- Are there SQL injection risks (raw queries, `.extra()`, string interpolation in filters)?
- Is any sensitive data (API keys, tokens, PII) logged, stored in plain text, or included in
  URLs?
- Are file upload paths validated? Could a user write outside the intended directory?
- Are permission checks (`login_required`, `permission_required`, `has_permission`) present on
  all views that require them?
- Does any new endpoint expose data that should be restricted?
