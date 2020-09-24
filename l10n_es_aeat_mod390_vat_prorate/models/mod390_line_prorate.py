# Copyright 2020 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from odoo import api, fields, models, exceptions, _


class L10nEsAeatMod390ReportLineProrate(models.Model):
    _name = 'l10n.es.aeat.mod390.report.line.prorate'
    _description = 'AEAT 390 report line prorate'

    report_id = fields.Many2one(
        string="Report 390",
        comodel_name="l10n.es.aeat.mod390.report",
        readonly=True
    )
    activity = fields.Char(
        string="Activity",
        required=True
    )
    cnae = fields.Char(
        string="CNAE",
        size=3,
        required=True
    )
    amount = fields.Float(
        string="Total amount of operations",
    )
    amount_deductable = fields.Float(string="Amount  deductable")
    prorate_type = fields.Selection(
        [
            ('G', 'General')
        ],
        string="Type",
        default='G',
        required=True
    )
    percent = fields.Float(
        string="Percent",
        default=100
    )

    @api.constrains('percent')
    def check_percent(self):
        for item in self:
            if not (0 < item.percent <= 100):
                raise exceptions.ValidationError(
                    _('VAT prorrate percent must be between 0.01 and 100')
                )
