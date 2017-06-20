# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import openerp.exceptions
from openerp.osv import fields, osv, orm
from requests import Session
from zeep import Client
from zeep.transports import Transport
from zeep.plugins import HistoryPlugin
from datetime import datetime

class aeat_sii_map(osv.Model):
    _name = 'aeat.sii.map'
    _description = 'Aeat SII Map'

    _columns = {
        'name': fields.char('Model'),
        'date_from': fields.date('Date from'),
        'date_to': fields.date('Date to'),
        'map_lines': fields.one2many('aeat.sii.map.lines', 'sii_map_id', 'Lines'),
    }     


    def _unique_date_range(self, cr, uid, ids, context=None):

        # TODO Revisar dominio para ambas fechas, er

        # for map in self.browse(cr, uid, ids, context):
            # domain = [('id', '!=', map.id)]
            # if map.date_from and map.date_to:
            #     domain += ['|', '&',
            #                ('date_from', '<=', map.date_to),
            #                ('date_from', '>=', map.date_from),
            #                '|', '&',
            #                ('date_to', '<=', map.date_to),
            #                ('date_to', '>=', map.date_from),
            #                '|', '&',
            #                ('date_from', '=', False),
            #                ('date_to', '>=', map.date_from),
            #                '|', '&',
            #                ('date_to', '=', False),
            #                ('date_from', '<=', map.date_to),
            #                ]
            # elif map.date_from:
            #     domain += [('date_to', '>=', map.date_from)]
            # elif map.date_to:
            #     domain += [('date_from', '<=', map.date_to)]
            #
            # if self.search(cr, uid, domain):
            #     return False
        return True

    _constraints = [
        (_unique_date_range, "Error! The dates of the record overlap with an existing record" , ['date_to','date_from'])
    ]

aeat_sii_map()

class aeat_sii_map_lines(osv.Model):
    _name = 'aeat.sii.map.lines'
    _description = 'Aeat SII Map Lines'

    _columns = {
        'name': fields.char('Name'),
        'code': fields.char('Code'),
        'taxes': fields.many2many('account.tax.template', 'aeat_rel_tax_template_map_line_sii', 'template_id', 'sii_map_line_id', string="Taxes"),
        'sii_map_id': fields.many2one('aeat.sii.map', 'Aeat SII Map'),
    }
aeat_sii_map_lines()


