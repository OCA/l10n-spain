# -*- coding: utf-8 -*-
# © 2017 - Otherway Creatives - Pedro Rodriguez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import SUPERUSER_ID
from openerp.api import Environment
import json
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

def migrate(cr, version):
    env = Environment(cr, SUPERUSER_ID, {})
    invoice_obj = env['account.invoice']
    invoices = invoice_obj.search([
        ('type', 'in', ['in_invoice', 'in_refund']),
        ('sii_state', 'not in', ['not sent']),
        ('sii_content_sent', '!=', False)
    ])
    if not invoices:
        return True
    for invoice in invoices:
        content_sent = json.loads(invoice.sii_content_sent)
        if 'FacturaRecibida' not in content_sent:
            continue
        if 'FechaRegContable' not in content_sent['FacturaRecibida']:
            continue
        reg_date = datetime.strptime(
            content_sent['FacturaRecibida']['FechaRegContable'], '%d-%m-%Y'
        ).strftime(DF)
        cr.execute(
            """
            UPDATE account_invoice
            SET sii_account_registration_date = '%(reg_date)s'
            WHERE id = %(invoice_id)s
            """ % {
                'invoice_id': invoice.id,
                'reg_date': reg_date,
            })
