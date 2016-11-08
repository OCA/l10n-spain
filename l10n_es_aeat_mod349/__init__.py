# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from . import models
from openerp import SUPERUSER_ID


def _assign_invoice_operation_keys(cr, registry):
    """On first install of the module, this method is called to assign a
    default value to invoices and fiscal position.
    """
    fp_obj = registry['account.fiscal.position']
    # TODO: Intentar depender lo menos posible del nombre
    fp_ids = fp_obj.search(cr, SUPERUSER_ID,
                           [('name', '=', "Régimen Intracomunitario")])
    if not fp_ids:
        return
    fp_obj.write(cr, SUPERUSER_ID, fp_ids, {'intracommunity_operations': True})
    invoice_obj = registry['account.invoice']
    invoice_ids = invoice_obj.search(cr, SUPERUSER_ID, [])
    for invoice in invoice_obj.browse(cr, SUPERUSER_ID, invoice_ids):
        if invoice.fiscal_position:
            op_key = invoice._get_operation_key(invoice.fiscal_position,
                                                invoice.type)
            invoice_obj.write(cr, SUPERUSER_ID, invoice.id,
                              {'operation_key': op_key})
