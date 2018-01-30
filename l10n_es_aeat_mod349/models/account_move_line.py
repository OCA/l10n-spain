# Copyright 2017 Luis M. Ontalba <luis.martinez@tecnativa.com>
# Copyright 2017 Eficent Business & IT Consult. Services <contact@eficent.com>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    """Inheritance of account move line to add some fields:
    - AEAT_349_operation_key: Operation key of invoice line
    """
    _inherit = 'account.move.line'

    l10n_es_aeat_349_operation_key = fields.Selection(
        selection=[
            ('A', 'A - Intra-Community acquisition'),
            ('E', 'E - Intra-Community supplies'),
            ('I', 'I - Intra-Community services acquisitions'),
            ('S', 'S - Intra-Community services'),
            ('T', 'T - Triangular operations'),
        ],
        string='AEAT 349 Operation key',
    )
