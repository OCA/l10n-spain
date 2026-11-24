# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """The plastic document type of the contacts is computed from the VAT and the
    additional identifiers of Odoo core, where l10n_es_aeat moves the AEAT
    identification by SQL, so the values stored in 19.0 are computed again."""
    partners = env["res.partner"].with_context(active_test=False).search([])
    env.add_to_compute(env["res.partner"]._fields["plastic_document_type"], partners)
    partners.flush_recordset(["plastic_document_type"])
