# -*- coding: utf-8 -*-
# © 2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class PaymentModeFaceCode(models.Model):
    _name = "payment.mode.face.code"

    code = fields.Char("Code", size=2, required=True)
    name = fields.Char("Name", required=True)


class PaymentMode(models.Model):
    _inherit = "payment.mode"

    face_code_id = fields.Many2one("payment.mode.face.code", "FACe code")
