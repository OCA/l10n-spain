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

from openerp import models, fields, api


class L10nEsAeatMod340Report(models.Model):

    _inherit = 'l10n.es.aeat.mod340.report'

    @api.onchange('contact_name')
    def on_change_name_contact(self):
        self.presenter_name = self.contact_name
        self.presenter_name_contact = self.contact_name

    @api.onchange('contact_phone')
    def on_change_phone_contact(self):
        self.presenter_phone_contact = self.contact_phone

    @api.onchange('representative_vat')
    def on_change_representative_vat(self):
        self.presenter_vat = self.representative_vat

    presenter_vat = fields.Char(string='VAT number', size=9,
                                states={'confirmed': [('readonly', True)]})
    presenter_name = fields.Char(string='Name And Surname', size=40)
    presenter_address_acronym = fields.Char(string='Address Acronym', size=2,
                                            help='Acronyms of the type of '
                                            'public roadway, example St.')
    presenter_address_name = fields.Char(string='Street Name', size=52)
    presenter_address_number = fields.Integer(string='Number', size=5)
    presenter_address_stair = fields.Char(string='Stair', size=2)
    presenter_address_floor = fields.Char(string='Floor', size=2)
    presenter_address_door = fields.Char(string='Door', size=2)
    presenter_city_id = fields.Many2one('res.better.zip', string='Location',
                                        select=1, help='Use the name or the '
                                        'zip to search the location')
    presenter_phone_contact = fields.Char(string='Phone Contact', size=9)
    presenter_name_contact = fields.Char(string='Name And Surname Contact',
                                         size=40)
