# -*- encoding: utf-8 -*-
##############################################################################
#
#  OpenERP, Open Source Management Solution.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api


class L10nEsAeatMod111Report(models.Model):

    _description = 'AEAT 111 report'
    _inherit = 'l10n.es.aeat.mod111.report'

    @api.multi
    def _get_partner_domain(self):
        res = super(L10nEsAeatMod111Report, self)._get_partner_domain()
        no_resident_partners = []
        employee_lst = self.env['hr.employee'].search([('is_resident', '=',
                                                        False)])
        for employee in employee_lst:
            if employee.user_id and employee.user_id.partner_id:
                no_resident_partners.append(employee.user_id.partner_id.id)
        res += [('partner_id', 'not in', no_resident_partners)]
        return res
