# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
# Copyright (c) 2006 ACYSOS S.L.. (http://acysos.com) All Rights Reserved.
#    Pedro Tarrafeta <pedro@acysos.com>
#
# Corregido para instalación TinyERP estándar 4.2.0: Zikzakmedia S.L. 2008
#   Jordi Esteve <jesteve@zikzakmedia.com>
#
# Añadidas cuentas de remesas y tipos de pago. 2008
#    Pablo Rocandio <salbet@gmail.com>
#
# Corregido para instalación OpenERP 5.0.0 sobre account_payment_extension:
# Zikzakmedia S.L. 2009 Jordi Esteve <jesteve@zikzakmedia.com>
#
# Adaptación para instalación OpenERP 6.0.0 sobre account_payment_extension:
# Zikzakmedia S.L. 2010 Jordi Esteve <jesteve@zikzakmedia.com>
#
# Añadidos conceptos extras del CSB 19: Acysos S.L. 2011
#   Ignacio Ibeas <ignacio@acysos.com>
#
#    $Id$
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

from openerp import models, fields


class PaymentMode(models.Model):
    _inherit = "payment.mode"

    csb_suffix = fields.Char(string='Suffix', size=3, default='000')
    csb32_assignor = fields.Char(string='Assignor', size=15)
    csb58_include_address = fields.Boolean(
        string='Include address', default=False,
        help='Add partner domicile records to the exported file (CSB 58)')
    csb58_alt_address_format = fields.Boolean(
        string='Alt. address format', default=False,
        help='Alternative domicile record format')
    csb58_ine = fields.Char('INE code', size=9)
    csb_require_bank_account = fields.Boolean(
        string='Require bank account', default=True,
        help='If your bank allows you to send orders without the bank account '
        'info, you may disable this option')
    csb34_type = fields.Selection(
        string='Type of CSB 34 payment', default='transfer',
        selection=[('transfer', 'Transfer'),
                   ('promissory_note', 'Promissory Note'),
                   ('cheques', 'Cheques'),
                   ('certified_payments', 'Certified Payments')])
    csb34_text1 = fields.Char(
        string='Line 1', size=36,
        help='Enter text and/or select a field of the invoice to include as a '
        'description in the letter. The possible values ​​are: ${amount}, '
        '${communication}, {communication2}, {date}, {ml_maturity_date}, '
        '{create_date}, {ml_date_created}')
    csb34_text2 = fields.Char(
        string='Line 2', size=36,
        help='Enter text and/or select a field of the invoice to include as a '
        'description in the letter. The possible values ​​are: ${amount}, '
        '${communication}, {communication2}, {date}, {ml_maturity_date}, '
        '{create_date}, {ml_date_created}')
    csb34_text3 = fields.Char(
        string='Line 3', size=36,
        help='Enter text and/or select a field of the invoice to include as a '
        'description in the letter. The possible values ​​are: ${amount}, '
        '${communication}, {communication2}, {date}, {ml_maturity_date}, '
        '{create_date}, {ml_date_created}')
    csb34_payroll_check = fields.Boolean(
        string='Payroll Check',
        help='Check it if you want to add the 018 data type in the file (the '
        'vat of the recipient is added in the 018 data type).')
    csb34_add_date = fields.Boolean(
        string='Add Date',
        help='Check it if you want to add the 910 data type in the file to '
        'include the payment date.')
    csb34_send_type = fields.Selection(
        string='Send type', default='mail',
        help='The sending type of the payment file',
        selection=[('mail', 'Ordinary Mail'),
                   ('certified_mail', 'Certified Mail'),
                   ('other', 'Other')])
    csb34_not_to_the_order = fields.Boolean(string='Not to the Order',
                                            default=True)
    csb34_barred = fields.Boolean(string='Barred', default=True)
    csb34_cost_key = fields.Selection(
        string='Concept of the Order', default='payer',
        selection=[('payer', 'Expense of the Payer'),
                   ('recipient', 'Expense of the Recipient')])
    csb34_concept = fields.Selection(
        string='Concepto of the order', default='other',
        selection=[('payroll', 'Payroll'), ('pension', 'Pension'),
                   ('other', 'Other')])
    csb34_direct_pay_order = fields.Boolean(
        string='Direct Pay Order', default=False, help='By default "Not"')
    csb19_extra_concepts = fields.Boolean(
        string='Extra Concepts', default=False,
        help='Check it if you want to add the invoice lines to the extra '
        'concepts (Max. 15 lines)')
