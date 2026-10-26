# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """The ATC declarations are now for the AEAT group. The ATC group was
    noupdate data, which an update does not delete, so it is removed once the
    declaration modules have moved their access rules to the AEAT group. The
    AEAT group and its privilege are noupdate data too, so an update does not
    write the AEAT/ATC names that an install gives them."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    group = env.ref("l10n_es_atc.group_account_atc", raise_if_not_found=False)
    if group:
        group.unlink()
    env.ref("l10n_es_aeat.res_groups_privilege_aeat").name = "AEAT/ATC Permissions"
    env.ref("l10n_es_aeat.group_account_aeat").name = "AEAT/ATC manager"
