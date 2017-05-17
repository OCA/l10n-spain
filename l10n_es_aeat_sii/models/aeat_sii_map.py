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
        'taxes': fields.many2many('account.tax.template', 'taxes_aeat_rel', 'tax_template_id', 'aeat_id' ,
                                  string="Taxes"),
        'sii_map_id': fields.many2one('aeat.sii.map', 'Aeat SII Map')
    }

class AeatSiiMap(osv.Model):
    _name = 'aeat.sii.map'
    _description = 'Aeat SII Map'

    # @api.one
    # @api.constrains('date_from', 'date_to')
    # def _unique_date_range(self):
    #     # Based in l10n_es_aeat module
    #     domain = [('id', '!=', self.id)]
    #     if self.date_from and self.date_to:
    #         domain += ['|', '&',
    #                    ('date_from', '<=', self.date_to),
    #                    ('date_from', '>=', self.date_from),
    #                    '|', '&',
    #                    ('date_to', '<=', self.date_to),
    #                    ('date_to', '>=', self.date_from),
    #                    '|', '&',
    #                    ('date_from', '=', False),
    #                    ('date_to', '>=', self.date_from),
    #                    '|', '&',
    #                    ('date_to', '=', False),
    #                    ('date_from', '<=', self.date_to),
    #                    ]
    #     elif self.date_from:
    #         domain += [('date_to', '>=', self.date_from)]
    #     elif self.date_to:
    #         domain += [('date_from', '<=', self.date_to)]
    #     date_lst = self.search(domain)
    #     if date_lst:
    #         raise exceptions.Warning(
    #             _("Error! The dates of the record overlap with an existing "
    #               "record."))

    _columns = {
        'name': fields.char(string='Model', required=True, size=128),
        'date_from': fields.date(string='Date from'),
        'date_to': fields.date(string='Date to'),
        'map_lines': fields.one2many('aeat.sii.map.lines', 'sii_map_id', string='Lines'),
    }