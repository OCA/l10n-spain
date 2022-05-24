# Copyright 2022 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openupgradelib import openupgrade

_xmlid_renames = [
    (
        "l10n_es_facturae_face.account_invoice_face_server",
        "l10n_es_facturae_face.face_ws_link",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_xmlids(env.cr, _xmlid_renames)
