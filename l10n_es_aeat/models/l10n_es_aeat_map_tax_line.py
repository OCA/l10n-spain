# Copyright 2013-2018 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from odoo import fields, models


class L10nEsAeatMapTaxLine(models.Model):
    _name = 'l10n.es.aeat.map.tax.line'
    _order = "field_number asc, id asc"
    _description = 'AEAT tax mapping line'

    field_number = fields.Integer(string="Field number", required=True)
    tax_ids = fields.Many2many(
        comodel_name='account.tax.template', string="Taxes templates",
    )
    name = fields.Char(string="Name", required=True)
    map_parent_id = fields.Many2one(
        comodel_name='l10n.es.aeat.map.tax', required=True)
    move_type = fields.Selection(
        selection=[
            ('all', 'All'),
            ('regular', 'Regular'),
            ('refund', 'Refund'),
        ],
        string="Operation type",
        default='all',
        required=True,
    )
    field_type = fields.Selection(
        selection=[
            ('base', 'Base'),
            ('amount', 'Amount'),
        ],
        string="Field type",
        default='amount',
        required=True,
    )
    sum_type = fields.Selection(
        selection=[
            ('credit', 'Credit'),
            ('debit', 'Debit'),
            ('both', 'Both (Credit - Debit)'),
        ],
        string="Summarize type",
        default='both',
        required=True,
    )
    exigible_type = fields.Selection(
        selection=[
            ('yes', 'Only exigible amounts'),
            ('no', 'Only non-exigible amounts'),
            ('both', 'Both exigible and non-exigible amounts'),
        ],
        required=True,
        string="Exigibility",
        default='yes',
    )
    inverse = fields.Boolean(string="Inverse summarize sign", default=False)
    to_regularize = fields.Boolean(string="To regularize")
