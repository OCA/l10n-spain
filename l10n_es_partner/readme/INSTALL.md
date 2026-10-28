This module depends on *base_bank_from_iban* from
<https://github.com/OCA/community-data-files>.

## Upgrade from Odoo 19

The Odoo 20 upgrade removes the core `res.bank` model. Before Odoo loads any
Odoo 20 module, take a database backup and pass the migration snapshot script
to the same Odoo update command that upgrades the database:

```text
--pre-upgrade-scripts=/path/to/l10n_es_partner/migrations/20.0.1.0.0/pre-migration.py
```

The normal core upgrade must include `l10n_es_partner` in the modules being
updated. The pre-upgrade script snapshots every `res.bank` row, its external
IDs and account links before `base` is loaded. The module post-migration
restores them into `l10n.es.bank`, rebuilds account links, fills only empty
account bank details, and verifies the restored counts. It drops the auxiliary
tables only after all checks pass. Third-party columns are copied when the new
model has a matching field name. If the snapshot contains a column without a
matching field on `l10n.es.bank`, the migration stops and keeps the snapshot
for an explicit mapping.

This command option only provides the early snapshot step. It does not perform
the full Odoo 19 to 20 core database upgrade; validate the complete sequence on
a disposable Odoo 19 database using the project's supported upgrade procedure.
