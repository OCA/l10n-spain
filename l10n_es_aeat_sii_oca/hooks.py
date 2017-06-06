# -*- coding: utf-8 -*-
# Copyright © 2017 Oihane Crucelaegui - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import SUPERUSER_ID


def add_key_to_existing_invoices(cr, registry):
    """This post-init-hook will update all existing invoices"""
    invoice_obj = registry['account.invoice']
    invoices = invoice_obj.search(cr, SUPERUSER_ID, [])
    if invoices:
        sii_key_obj = registry['aeat.sii.mapping.registration.keys']
        sale_key = sii_key_obj.search(
            cr, SUPERUSER_ID, [('code', '=', '01'), ('type', '=', 'sale')],
            limit=1)
        purchase_key = sii_key_obj.search(
            cr, SUPERUSER_ID, [('code', '=', '01'), ('type', '=', 'purchase')],
            limit=1)
        if purchase_key:
            cr.execute("""
                UPDATE account_invoice
                SET registration_key = {}
                WHERE type IN ('in_invoice', 'in_refund');""".format(
                purchase_key[0]))
        if sale_key:
            cr.execute("""
                UPDATE account_invoice
                SET registration_key = {}
                WHERE type NOT IN ('in_invoice', 'in_refund');""".format(
                sale_key[0]))
        cr.execute("""
            ALTER TABLE account_invoice
            ALTER COLUMN registration_key SET NOT NULL;
            """)
