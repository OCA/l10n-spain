# Copyright 2022 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openupgradelib import openupgrade

_xmlid_renames = [
    (
        "l10n_es_facturae.facturae_backend_type",
        "l10n_es_facturae_face.facturae_backend_type",
    ),
    (
        "l10n_es_facturae.facturae_exchange_type",
        "l10n_es_facturae_face.facturae_exchange_type",
    ),
    (
        "l10n_es_facturae.edi_exchange_record_view_form",
        "l10n_es_facturae_face.edi_exchange_record_view_form",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    module = env["ir.module.module"].search([("name", "=", "l10n_es_facturae_face")])
    if module.state != "uninstalled":
        # This should only happen if we only have e.FAct installed but not FACe
        openupgrade.rename_xmlids(env.cr, _xmlid_renames)
