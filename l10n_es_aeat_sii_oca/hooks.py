# Copyright 2017 Oihane Crucelaegui - AvanzOSC
# Copyright 2021 Tecnativa - João Marques
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import SUPERUSER_ID, api


def add_key_to_existing_invoices(cr, registry):
    """This post-init-hook will update all existing invoices"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    invoice_obj = env["account.move"]
    invoices = invoice_obj.search(
        [
            (
                "move_type",
                "in",
                ("in_invoice", "in_refund", "out_invoice", "out_refund"),
            )
        ]
    )
    if invoices:
        sii_key_obj = env["aeat.sii.mapping.registration.keys"]
        sale_key = sii_key_obj.search(
            [("code", "=", "01"), ("type", "=", "sale")], limit=1
        )
        purchase_key = sii_key_obj.search(
            [("code", "=", "01"), ("type", "=", "purchase")], limit=1
        )
        if purchase_key:
            cr.execute(
                """
                UPDATE account_move
                SET sii_registration_key = %s
                WHERE move_type IN ('in_invoice', 'in_refund');""",
                (purchase_key[0].id,),
            )
        if sale_key:
            cr.execute(
                """
                UPDATE account_move
                SET sii_registration_key = %s
                WHERE move_type IN ('out_invoice', 'out_refund');""",
                (sale_key[0].id,),
            )
