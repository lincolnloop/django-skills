# Django Admin Playbook

Apply whenever `admin.py` files are added or changed. Rule shape follows `django-development`:
**Do/Don't**, **Why**, **Except**, **Evidence**.

---

### A `save_model` override must call `super()` `admin/save-model-calls-super`
- **Do:** check that a custom `ModelAdmin.save_model` (or `delete_model`, `save_formset`)
  override calls `super().save_model(...)` rather than reimplementing the save itself.
- **Why:** the base implementation does more than call `obj.save()` — it's the hook point the
  rest of `ModelAdmin` (history recording, formset saving order) depends on being invoked
  consistently.
- **Except:** an override that deliberately needs full control over the save (rare) should say so
  explicitly in a comment, since skipping `super()` is otherwise almost always a mistake.
- **Evidence:** Django docs, `ModelAdmin.save_model()` — the default implementation `obj.save()`
  is itself trivial, but overrides are expected to call it via `super()` unless replacing it
  deliberately.

### A custom admin action must report what it did via `message_user` `admin/action-user-feedback`
- **Do:** check that a custom `@admin.action` calls `self.message_user(request, ...)` to report
  its outcome (count affected, errors, skipped items).
- **Why:** admin actions run against a selected queryset with no other feedback mechanism — with
  no message, a staff user has no way to confirm the action did what they expected, or to notice
  it partially failed.
- **Evidence:** Django docs, "Actions" — `ModelAdmin.message_user()`.

### A dangerous bulk action needs protection against accidental triggering `admin/dangerous-action-protection`
- **Do:** check that an action capable of large-scale or irreversible effects (bulk delete,
  bulk status change, anything that sends external notifications) has a confirmation step, is
  scoped narrowly, or otherwise can't be triggered by an accidental click on the wrong queryset.
- **Why:** admin actions apply to whatever's selected in the changelist, including an
  accidentally-select-all on a filtered or paginated view — a destructive action with no
  confirmation step turns one misclick into a large, possibly irreversible, change.
- **Except:** Django's own bulk delete confirmation page already protects the built-in delete
  action; this concern is for custom actions that bypass an equivalent confirmation step.
- **Evidence:** Django docs, "Actions" — intermediate confirmation pages are an explicitly
  supported pattern precisely for this reason.
