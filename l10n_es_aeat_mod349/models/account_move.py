# Copyright 2017 Tecnativa - Luis M. Ontalba
# Copyright 2017 Eficent Business & IT Consult. Services <contact@eficent.com>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# Copyright 2019 David Gómez <david.gomez@aselcis.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):

    _inherit = 'account.move'

    eu_triangular_deal = fields.Boolean(
        string='EU Triangular deal',
        help='This invoice constitutes a triangular operation for the '
             'purposes of intra-community operations.',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
