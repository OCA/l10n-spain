# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.osv import osv, fields


class AeatSiiMapLines(osv.Model):
    _name = 'aeat.sii.map.lines'
    _description = 'Aeat SII Map Lines'

    _columns = {
        'code': fields.char(string='Code', required=True, size=32),
        'name': fields.char(string='Name', size=128),
        'taxes': fields.many2many('account.tax.template', 'taxes_aeat_rel', 'tax_template_id', 'aeat_id',
                                  string="Taxes"),
        'sii_map_id': fields.many2one('aeat.sii.map', 'Aeat SII Map')
    }


class AeatSiiMap(osv.Model):
    _name = 'aeat.sii.map'
    _description = 'Aeat SII Map'

    _columns = {
        'name': fields.char(string='Model', required=True, size=128),
        'date_from': fields.date(string='Date from'),
        'date_to': fields.date(string='Date to'),
        'map_lines': fields.one2many('aeat.sii.map.lines', 'sii_map_id', string='Lines'),
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
