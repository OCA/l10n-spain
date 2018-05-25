# -*- coding: utf-8 -*-
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    sii_payment_mode_id = fields.Many2one(
        comodel_name='aeat.sii.payment.mode.key',
        string="SII payment mode"
    )
