# Copyright 2022 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.set_xml_ids_noupdate_value(
        env,
        "l10n_es_facturae_face",
        [
            "face_backend",
            "facturae_face_update_exchange_type",
            "facturae_face_cancel_exchange_type",
        ],
        False,
    )
    openupgrade.load_data(
        env.cr,
        "l10n_es_facturae_face",
        "data/edi.xml",
    )
