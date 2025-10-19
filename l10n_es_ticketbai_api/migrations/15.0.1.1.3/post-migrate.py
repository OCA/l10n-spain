# Copyright 2023 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo
from odoo import release


def migrate(cr, version):
    if not version:
        return
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    installations = env["tbai.installation"].search([])
    for installation in installations:
        installation.version = release.version
