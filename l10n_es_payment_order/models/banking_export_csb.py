# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2013 Akretion (http://www.akretion.com)
#    @author: Alexis de Lattre <alexis.delattre@akretion.com>
#    Copyright (c) 2015 Acysos S.L. (http://acysos.com) All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
from unidecode import unidecode


class BankingExportCsb(models.Model):
    """CSB export"""
    _name = 'banking.export.csb'
    _description = __doc__
    _rec_name = 'filename'

    @api.one
    @api.depends('payment_order_ids', 'payment_order_ids.reference')
    def _generate_filename(self):
        if self.payment_order_ids:
            ref = self.payment_order_ids[0].reference
            label = unidecode(ref.replace('/', '-')) if ref else 'error'
            filename = 'csb_%s.txt' % label
        else:
            filename = 'csb.txt'
        self.filename = filename

    payment_order_ids = fields.Many2many(
        comodel_name='payment.order',
        relation='account_payment_order_csb_rel',
        column1='banking_export_csb_id', column2='account_order_id',
        string='Payment Orders',
        readonly=True)
    create_date = fields.Datetime(string='Generation Date', readonly=True)
    file = fields.Binary(string='CSB File', readonly=True)
    filename = fields.Char(compute=_generate_filename, size=256,
                           string='Filename', readonly=True, store=True)
    state = fields.Selection([('draft', 'Draft'), ('sent', 'Sent')],
                             string='State', readonly=True, default='draft')
