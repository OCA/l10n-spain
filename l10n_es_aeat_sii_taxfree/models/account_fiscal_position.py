# © 2019 - FactorLibre - Daniel Duque <daniel.duque@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    sii_refund_as_regular = fields.Boolean(string="Send refunds as regular invoices")
