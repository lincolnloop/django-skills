# Django Admin Playbook

Apply whenever `admin.py` files are added or changed.

- Are custom `save_model` overrides calling `super()`?
- Do custom actions give user feedback via `message_user`?
- Are dangerous bulk actions protected from accidental use?
