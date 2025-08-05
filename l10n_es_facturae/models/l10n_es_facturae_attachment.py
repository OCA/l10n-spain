# Copyright 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class L10nEsFacturaeAttachment(models.Model):
    _name = "l10n.es.facturae.attachment"
    _description = "Facturae Attachment"

    move_id = fields.Many2one("account.move", required=True, ondelete="cascade")
    file = fields.Binary(required=True)
    filename = fields.Char()
