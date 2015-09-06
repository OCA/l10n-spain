# -*- coding: utf-8 -*-
# (c) 2015 Antiun Ingeniería S.L. - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api


class ComputeVatProrrate(models.TransientModel):
    _name = "l10n.es.aeat.compute.vat.prorrate"

    fiscalyear_id = fields.Many2one(
        comodel_name="account.fiscalyear", string="Fiscal year", required=True)

    @api.multi
    def button_compute(self):
        self.ensure_one()
        mod303 = self.env['l10n.es.aeat.mod303.report'].browse(
            self.env.context['active_id'])
        codes = ['RGIDBI10', 'RGIDBI21', 'RGIDBI4', 'MBYCRBI']
        move_lines = mod303._get_tax_code_lines(
            codes, periods=self.fiscalyear_id.period_ids)
        taxed = sum(move_lines.mapped('tax_amount'))
        move_lines = mod303._get_tax_code_lines(
            ['OESDAD'], periods=self.fiscalyear_id.period_ids)
        exempt = sum(move_lines.mapped('tax_amount'))
        mod303.vat_prorrate_percent = taxed / (taxed + exempt) * 100
        return True
