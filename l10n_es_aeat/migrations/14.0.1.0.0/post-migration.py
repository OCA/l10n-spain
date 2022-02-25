# Copyright 2022 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade  # pylint: disable=W7936


@openupgrade.migrate()
def migrate(env, version):
    partner = env.ref("l10n_es_aeat.res_partner_aeat", raise_if_not_found=False)
    if partner and partner.street:
        openupgrade.logged_query(
            env.cr,
            """
            UPDATE res_partner
            SET street = trim(both from street)
            WHERE id = %s AND street != trim(both from street)""",
            (partner.id,),
        )
