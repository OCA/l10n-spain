# Copyright 2015-2020 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

import math
from odoo import api, fields, models


class ComputeVatProrrate(models.TransientModel):
    _name = "l10n.es.aeat.compute.vat.prorrate"
    _description = "Wizard for computing VAT prorrate"

    def _default_year(self):
        return int(fields.Date.today().year)

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
        affected_taxes = [
            'l10n_es.account_tax_template_s_iva4b',
            'l10n_es.account_tax_template_s_iva4s',
            'l10n_es.account_tax_template_s_iva10b',
            'l10n_es.account_tax_template_s_iva10s',
            'l10n_es.account_tax_template_s_iva21b',
            'l10n_es.account_tax_template_s_iva21s',
            'l10n_es.account_tax_template_s_iva21isp',
        ]
        MapLine = self.env['l10n.es.aeat.map.tax.line']
        mapline_vals = {
            'move_type': 'all',
            'field_type': 'base',
            'sum_type': 'both',
            'exigible_type': 'yes',
            'tax_ids': [(4, self.env.ref(x).id) for x in affected_taxes],
        }
        map_line = MapLine.new(mapline_vals)
        move_lines = mod303._get_tax_lines(False, date_from, date_to, map_line)
        taxed = (sum(move_lines.mapped('credit')) -
                 sum(move_lines.mapped('debit')))
        # Get base amount of exempt operations
        mapline_vals['tax_ids'] = [
            (4, self.env.ref('l10n_es.account_tax_template_s_iva0').id)]
        map_line = MapLine.new(mapline_vals)
        move_lines = mod303._get_tax_lines(False, date_from, date_to, map_line)
        exempt = (sum(move_lines.mapped('credit')) -
                  sum(move_lines.mapped('debit')))
        # compute prorrate percentage performing ceiling operation
        mod303.vat_prorrate_percent = math.ceil(taxed / (taxed + exempt) * 100)
        return True
