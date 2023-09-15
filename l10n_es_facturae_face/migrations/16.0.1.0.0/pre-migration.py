# Copyright 2023 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if env.ref(
        "l10n_es_facturae_face.facturae_face_exchange_type_rule",
        raise_if_not_found=False,
    ):
        # In this case, the upgrade passed on a previous version
        return
    for exchange_type in env.ref(
        "l10n_es_facturae_face.facturae_exchange_type"
    ) | env.ref("l10n_es_facturae_face.facturae_face_update_exchange_type"):
        exchange_type.write(
            {
                "model_ids": [(5, 0, 0)],
                "enable_snippet": False,
                "enable_domain": False,
            }
        )
        exchange_type.rule_ids.unlink()
