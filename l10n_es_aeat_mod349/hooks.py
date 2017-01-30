# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    """On first install of the module, this method is called to assign a
    default value to invoices and fiscal position.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    # TODO: Intentar depender lo menos posible del nombre
    fps = env['account.fiscal.position'].search([
        ('name', '=', "Régimen Intracomunitario")
    ])
    if not fps:
        return
    fps.write({'intracommunity_operations': True})
    invoices = env['account.invoice'].search([])
    for invoice in invoices.filtered('fiscal_position_id'):
        invoice.operation_key = invoice._get_operation_key(
            invoice.fiscal_position_id, invoice.type
        )
