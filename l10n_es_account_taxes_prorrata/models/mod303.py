# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api


class L10nEsAeatMod303Report(models.Model):

    _inherit = 'l10n.es.aeat.mod303.report'

    prorrata_type = fields.Selection([('none', 'Ninguno'),
                                      ('general', 'Prorrata General'),
                                      ('special', 'Prorrata Especial')],
                                     string="Tipo prorrata", default='none')
    prorrata_deducible = fields.Float(string="Deducible")
    prorrata_no_deducible = fields.Float(string="No deducible")
    prorrata_porcentaje = fields.Float(string="Porcentaje")

    @api.multi
    def calculate(self):
        tax_code_obj = self.env['account.tax.code']
        res = super(L10nEsAeatMod303Report, self).calculate()
        if self.prorrata_type == 'none':
            return res
        deducible_codes = tax_code_obj.search([('prorrata_tax_type',
                                                'in', ('b_dedu', 'c_dedu'))])
        no_deducible_codes = tax_code_obj.search([('prorrata_tax_type',
                                                   'in', ('b_no_dedu',
                                                          'c_no_dedu'))])
        report_lines = self._get_report_lines()
        deducible = 0.0
        no_deducible = 0.0
        imp_deducible = 0.0
        imp_no_deducible = 0.0
        for ded_code in deducible_codes:
            deducible += report_lines.get(ded_code.code, 0.0)
            if ded_code.prorrata_tax_type == 'c_dedu':
                imp_deducible += report_lines.get(ded_code.code, 0.0)
        for no_ded_code in no_deducible_codes:
            no_deducible += report_lines.get(no_ded_code.code, 0.0)
            if no_ded_code.prorrata_tax_type == 'c_no_dedu':
                imp_no_deducible += report_lines.get(no_ded_code.code, 0.0)
        self.prorrata_deducible = deducible
        self.prorrata_no_deducible = no_deducible
        self.prorrata_porcentaje = (deducible and no_deducible / deducible
                                    * 100 or 0.0)
        self.total_deducir = (imp_no_deducible * self.prorrata_porcentaje
                              / 100) + imp_deducible
        if self.prorrata_type == 'general':
            self.total_deducir = ((imp_no_deducible + imp_deducible) *
                                  self.prorrata_porcentaje / 100)
        return res
