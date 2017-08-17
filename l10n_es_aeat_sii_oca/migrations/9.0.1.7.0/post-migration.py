# -*- coding: utf-8 -*-
# © 2017 - Otherway Creatives - Pedro Rodriguez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import SUPERUSER_ID, fields
from openerp.api import Environment
import json
from datetime import datetime


def migrate(cr, version):
    env = Environment(cr, SUPERUSER_ID, {})
    invoice_obj = env['account.invoice']
    invoices = invoice_obj.search([
        ('type', 'in', ['in_invoice', 'in_refund']),
        ('sii_state', 'not in', ['not sent']),
        ('sii_content_sent', '!=', False),
        ('sii_account_registration_date', '=', False)
    ])
    for invoice in invoices:
        content_sent = json.loads(invoice.sii_content_sent)
        if 'FacturaRecibida' not in content_sent:
            continue
        if 'FechaRegContable' not in content_sent['FacturaRecibida']:
            continue
        reg_date = fields.Date.to_string(
            datetime.strptime(
                content_sent['FacturaRecibida']['FechaRegContable'], '%d-%m-%Y'
            )
        )
        invoice.sii_account_registration_date = reg_date
