# Copyright 2020 Javier de las Heras <jheras@alquemy.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    silicie_partner_identification_type = fields.Selection(
        selection=[
            ('national', 'National'),
            ('canarias', 'Canarias'),
            ('intra', 'Intracom'),
            ('export', 'Export'),
        ],
        string="SILICIE partner Identification Type",
    )
