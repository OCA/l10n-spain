# © 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo


def migrate(cr, version):
    if not version:
        return

    with odoo.api.Environment.manage():
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        for company in env['res.company'].search([]):
            company.onchange_tbai_tax_agency()
