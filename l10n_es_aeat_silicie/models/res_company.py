# Copyright 2020 Javier de las Heras <jheras@alquemy.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    silicie_enabled = fields.Boolean(
        string='Enable SILICIE',
    )
    silicie_test = fields.Boolean(
        string='Is Test Environment?',
    )
    silicie_method = fields.Selection(
        string='Method',
        selection=[
            ('auto', 'Automatic'),
            ('manual', 'Manual'),
        ],
        default='manual',
        help="By default, the move is sent/queued in validation process. "
             "With manual method, there's a button to send move.")
    silicie_send_mode = fields.Selection(
        string="Send mode",
        selection=[
            ('auto', 'On validate'),
            ('fixed', 'At fixed time'),
            ('delayed', 'With delay'),
        ], default='auto',
    )
    cae = fields.Char(
        string='CAE',
    )
    cae_for_tests = fields.Char(
        string='CAE For Tests',
    )
    aeat_office = fields.Char(
        string='AEAT Office'
    )
    silicie_inventory_disabled = fields.Boolean(
        string='SILICIE Products Inventory Disable',
    )
