# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2013 Acysos S.L. (http://acysos.com)
#                       Ignacio Ibeas Izquierdo <ignacio@acysos.com>
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

from openerp.osv import fields, orm


class AccountTaxCodeTemplate(orm.Model):
    _inherit = 'account.tax.code.template'

    _columns = {
        'mod340': fields.boolean("Include in mod340"),
        'surcharge_tax_id': fields.many2one(
            'account.tax.code',
            'Surcharge tax of'),
    }


class AccountTaxCode(orm.Model):
    _inherit = 'account.tax.code'

    _columns = {
        'mod340': fields.boolean("Include in mod340"),
        'surcharge_tax_id': fields.many2one(
            'account.tax.code',
            'Surcharge tax of'),
    }


class AccountTax(orm.Model):
    _inherit = 'account.tax'

    _columns = {
        'is_340_reserve_charge': fields.boolean(
            "Include in mod340 as reserve charge"),
    }


class AccountAccounte(orm.Model):
    _inherit = 'account.account'

    _columns = {
        'is_340_leasing_account': fields.boolean(
            "Include in mod340 as leasing account"),
    }
