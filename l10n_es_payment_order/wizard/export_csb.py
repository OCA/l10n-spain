# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2006 ACYSOS S.L. (http://acysos.com) All Rights Reserved.
#                       Pedro Tarrafeta <pedro@acysos.com>
#                       Ignacio Ibeas <ignacio@acysos.com>
#    Copyright (c) 2008 Pablo Rocandio. All Rights Reserved.
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights
#                       Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#
# Corregido para instalación TinyERP estándar 4.2.0: Zikzakmedia S.L. 2008
#   Jordi Esteve <jesteve@zikzakmedia.com>
#
# Añadidas cuentas de remesas y tipos de pago. 2008
#    Pablo Rocandio <salbet@gmail.com>
#
# Rehecho de nuevo para instalación OpenERP 5.0.0 sobre
#   account_payment_extension: Zikzakmedia S.L. 2009
#   Jordi Esteve <jesteve@zikzakmedia.com>
#
# Añadidos conceptos extras del CSB 19: Acysos S.L. 2011
#   Ignacio Ibeas <ignacio@acysos.com>
#
# Migración de wizard.interface para la 6.1: Pexego Sistemas Informáticos. 2012
#   Marta Vázquez Rodríguez <marta@pexego.es>
#
# Refactorización. Acysos S.L. (http://www.acysos.com) 2012
#   Ignacio Ibeas <ignacio@acysos.com>
#
# Migración OpenERP 7.0. Acysos S.L. (http://www.acysos.com) 2013
#   Ignacio Ibeas <ignacio@acysos.com>
#
# Migración OpenERP 8.0. Acysos S.L. (http://www.acysos.com) 2015
#   Ignacio Ibeas <ignacio@acysos.com>
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
from openerp import models, fields, api, _
from openerp import workflow
import base64
from log import *


class BankingExportCsbWizard(models.TransientModel):
    _name = 'banking.export.csb.wizard'
    _description = 'Export CSB File'

    join = fields.Boolean(
        string='Join payment lines of the same partner and bank account')
    note = fields.Text('Log')
    file_id = fields.Many2one('banking.export.csb', 'Payment order file',
                              readonly=True)
    file = fields.Binary(string="File", readonly=True, related='file_id.file')
    filename = fields.Char(string="Filename", readonly=True,
                           related='file_id.filename')
    payment_order_ids = fields.Many2many('payment.order', readonly=True)
    state = fields.Selection(
       string='State', readonly=True, default='create',
       selection=[('create', 'Create'), ('finish', 'Finish')])

    @api.model
    def create(self, vals):
        payment_order_ids = self._context.get('active_ids', [])

        vals.update({
            'payment_order_ids': [(6, 0, payment_order_ids)],
        })
        return super(BankingExportCsbWizard, self).create(vals)

    @api.multi
    def create_csb(self):
        converter = self.env['payment.converter.spain']
        txt_file = ''

        form_obj = self
        try:
            payment_order = self.env['payment.order'].browse(
                self._context.get('active_id'))
            if not payment_order.line_ids:
                raise Log(_('User error:\n\nWizard can not generate export '
                            'file, there are not payment lines.'), True)

            # Comprobamos que exista número de C.C. y que tenga 20 dígitos
            if not payment_order.mode.bank_id:
                raise Log(_('User error:\n\nThe bank account of the company '
                            '%s is not defined.') %
                          (payment_order.mode.partner_id.name), True)
            cc = converter.digits_only(payment_order.mode.bank_id.acc_number)
            if len(cc) != 20:
                raise Log(_('User error:\n\nThe bank account number of the '
                            'company %s has not 20 digits.') %
                          (payment_order.mode.partner_id.name), True)

            # Comprobamos que exista el CIF de la compañía asociada al C.C.
            # del modo de pago
            if not payment_order.mode.bank_id.partner_id.vat:
                raise Log(_('User error:\n\nThe company VAT number related to'
                            ' the bank account of the payment mode is not '
                            'defined.'), True)

            pay_lines = []
            if form_obj.join:
                # Lista con todos los partners+bancos diferentes de la remesa
                partner_bank_l = reduce(
                    lambda l, x: x not in l and l.append(x) or l,
                    [(line.partner_id, line.bank_id)
                     for line in payment_order.line_ids], [])
                # Cómputo de la lista de pay_lines agrupados por mismo
                # partner+banco.
                # Los importes se suman, los textos se concatenan con un
                # espacio en blanco y las fechas se escoge el máximo
                for partner, bank in partner_bank_l:
                    lineas = [recibo for recibo in payment_order.line_ids
                              if (recibo.partner_id == partner and
                                  recibo.bank_id == bank)]
                    pay_lines.append({
                        'partner_id': partner,
                        'bank_id': bank,
                        'name': partner.ref or str(partner.id),
                        'amount': reduce(lambda x, y: x+y,
                                         [l.amount for l in lineas], 0),
                        'communication': reduce(lambda x, y: x+' '+(y or ''),
                                                [l.name+' '+l.communication
                                                 for l in lineas], ''),
                        'communication2': reduce(lambda x, y: x+' '+(y or ''),
                                                 [l.communication2
                                                  for l in lineas], ''),
                        'date': max([l.date for l in lineas]),
                        'ml_maturity_date': max([l.ml_maturity_date
                                                 for l in lineas]),
                        'create_date': max([l.create_date for l in lineas]),
                        'ml_date_created': max([l.ml_date_created
                                                for l in lineas]),
                        'ml_inv_ref': [l.ml_inv_ref for l in lineas]
                    })
            else:
                # Cada línea de pago es un recibo
                for l in payment_order.line_ids:
                    pay_lines.append({
                        'partner_id': l.partner_id,
                        'bank_id': l.bank_id,
                        'name': l.partner_id.ref or str(l.partner_id.id),
                        'amount': l.amount,
                        'communication': l.name+' '+l.communication,
                        'communication2': l.communication2,
                        'date': l.date,
                        'ml_maturity_date': l.ml_maturity_date,
                        'create_date': l.create_date,
                        'ml_date_created': l.ml_date_created,
                        'ml_inv_ref': [l.ml_inv_ref]
                    })

            if payment_order.mode.csb_require_bank_account:
                for line in pay_lines:
                    bank = line['bank_id']
                    ccc = bank and bank.acc_number or False
                    if not ccc:
                        raise Log(_('User error:\n\nThe bank account number '
                                    'of the customer %s is not defined and '
                                    'current payment mode enforces all lines '
                                    'to have a bank account.') %
                                  (line['partner_id'].name), True)
                    ccc = converter.digits_only(ccc)
                    if len(ccc) != 20:
                        raise Log(_('User error:\n\nThe bank account number '
                                    'of the customer %s has not 20 digits.') %
                                  (line['partner_id'].name), True)

            if payment_order.mode.type.code == 'csb19':
                csb = self.env['csb.19']
            elif payment_order.mode.type.code == 'csb32':
                csb = self.env['csb.32']
            elif payment_order.mode.type.code == 'csb34':
                csb = self.env['csb.34']
            elif payment_order.mode.type.code == 'csb3401':
                csb = self.env['csb.3401']
            elif payment_order.mode.type.code == 'csb58':
                csb = self.env['csb.58']
            else:
                raise Log(_('User error:\n\nThe payment mode is not CSB 19, '
                            'CSB 32, CSB 34 or CSB 58'), True)
            txt_file = csb.create_file(payment_order, pay_lines)

        except Log, log:
            form_obj.note = unicode(log)
            form_obj.state = 'create'
            action = {
                'name': 'CSB File',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': self._name,
                'res_id': self.id,
                'target': 'new',
            }
            return action
        else:
            # Ensure line breaks use MS-DOS (CRLF) format as standards require.
            txt_file = txt_file.replace('\r\n', '\n').replace('\n', '\r\n')

            file_payment_order = base64.encodestring(txt_file.encode('utf-8'))
            # Borrar posible anterior adjunto de la exportación
            export_csb_obj = self.env['banking.export.csb']
            # Adjuntar nuevo archivo de remesa
            filename = payment_order.mode.type.code + '_'
            filename += payment_order.reference
            file_id = export_csb_obj.create({
                'file': file_payment_order,
                'filename': filename,
                'payment_order_ids': [
                    (6, 0, [order.id for order in self.payment_order_ids])],
                'state': 'draft'})
            log = _('Successfully Exported\n\nSummary:\n Total amount paid: '
                    '%.2f\n Total Number of Payments: %d\n') % (
                        payment_order.total, len(pay_lines))

            self.filename = filename
            self.file_id = file_id
            self.state = 'finish'

        action = {
            'name': 'CSB File',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': self._name,
            'res_id': self.id,
            'target': 'new',
        }
        return action

    @api.model
    def cancel_csb(self, ids):
        """Cancel the CSB file: just drop the file"""
        csb_export = self.browse(ids[0])
        csb_export.file_id.unlink()
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def save_csb(self, ids):
        """Save the CSB file: send the done signal to all payment
        orders in the file. With the default workflow, they will
        transition to 'done', while with the advanced workflow in
        account_banking_payment they will transition to 'sent' waiting
        reconciliation.
        """
        csb_export = self.browse(ids[0])
        csb_export.file_id.state = 'sent'
        for order in csb_export.payment_order_ids:
            workflow.trg_validate(self.env.uid, 'payment.order', order.id,
                                  'done', self.env.cr)

        return {'type': 'ir.actions.act_window_close'}
