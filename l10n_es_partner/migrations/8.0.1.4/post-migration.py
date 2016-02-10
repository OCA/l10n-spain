# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Diagram Software, S.L. (http://diagram.es)
#                       Cristian Moncho <cristian.moncho@diagram.es>
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

from openerp import api, SUPERUSER_ID

__name__ = ('Evita el borrado de los bancos ya existentes.')


def prevent_banks_deletion(env):
    env['ir.model.data'].search([
        ('module', '=', 'l10n_es_partner'),
        ('name', '=like', 'res_bank_es_%'),
        ('noupdate', '=', False)
    ]).write({'noupdate': True})


def migrate(cr, version):
    if not version:
        return
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        prevent_banks_deletion(env)
