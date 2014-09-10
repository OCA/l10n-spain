# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011-2014 Acysos S.L. (http://acysos.com)
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

from openerp.osv import orm, fields


class L10nEsAeatMod340Report(orm.Model):
    _inherit = 'l10n.es.aeat.mod340.report'

    def on_change_name_contact(self, cr, uid, ids, name_contact):
        return {'value': {'presenter_name': name_contact,
                          'presenter_name_contact': name_contact}}

    def on_change_phone_contact(self, cr, uid, ids, phone_contact):
        return {'value': {'presenter_phone_contact': phone_contact}}

    def on_change_representative_vat(self, cr, uid, ids, representative_vat):
        return {'value': {'presenter_vat': representative_vat}}

    _columns = {
        'presenter_vat': fields.char(
            'VAT number', size=9,
            states={'confirmed': [('readonly', True)]}),
        'presenter_name': fields.char('Name And Surname', size=40),
        'presenter_address_acronym': fields.char(
            'Address Acronym', size=2,
            help='Acronyms of the type of public roadway, example St.'),
        'presenter_address_name': fields.char('Street Name', size=52),
        'presenter_address_number': fields.integer('Number', size=5),
        'presenter_address_stair': fields.char('Stair', size=2),
        'presenter_address_floor': fields.char('Floor', size=2),
        'presenter_address_door': fields.char('Door', size=2),
        'presenter_city_id': fields.many2one(
            'res.better.zip', 'Location', select=1,
            help='Use the name or the zip to search the location'),
        'presenter_phone_contact': fields.char('Phone Contact', size=9),
        'presenter_name_contact': fields.char(
            'Name And Surname Contact', size=40),
    }
