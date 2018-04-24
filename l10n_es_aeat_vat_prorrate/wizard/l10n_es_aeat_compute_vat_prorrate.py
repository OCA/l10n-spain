# -*- coding: utf-8 -*-
# Copyright 2015-2017 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import math
from odoo import api, fields, models


class ComputeVatProrrate(models.TransientModel):
    _name = "l10n.es.aeat.compute.vat.prorrate"

    def _default_year(self):
        return int(fields.Date.today()[:4])

    year = fields.Integer(
        required=True,
        default=_default_year,
    )

    @api.multi
    def button_compute(self):
        self.ensure_one()
        date_from = '%s-01-01' % self.year
        date_to = '%s-12-31' % self.year
        mod303 = self.env['l10n.es.aeat.mod303.report'].browse(
            self.env.context['active_id']
        )
        # Get base amount for taxed operations
        taxed_taxes_codes = [
            'S_IVA4B', 'S_IVA4S',
            'S_IVA10B', 'S_IVA10S',
            'S_IVA21B', 'S_IVA21S', 'S_IVA21ISP',
        ]
        MapLine = self.env['l10n.es.aeat.map.tax.line']
        map_line = MapLine.new({
            'move_type': 'all',
            'field_type': 'base',
            'sum_type': 'both',
            'exigible_type': 'yes',
        })
        move_lines = mod303._get_tax_lines(
            taxed_taxes_codes, date_from, date_to, map_line,
        )
        taxed = (sum(move_lines.mapped('credit')) -
                 sum(move_lines.mapped('debit')))
        # Get base amount of exempt operations
        move_lines = mod303._get_tax_lines(
            ['S_IVA0'], date_from, date_to, map_line,
        )
        exempt = (sum(move_lines.mapped('credit')) -
                  sum(move_lines.mapped('debit')))
        # compute prorrate percentage performing ceiling operation
        mod303.vat_prorrate_percent = math.ceil(taxed / (taxed + exempt) * 100)
        return True
