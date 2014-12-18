# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright 2011 Soluntec - Soluciones Tecnológicas (http://www.soluntec.es)
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################

from openerp.osv import fields, orm


class AccountJournal(orm.Model):
    """Se modifica la clase de diarios contables para añadir nuevos campos que
    serán luego utilizados para determinar el comportamiento de los comprobantes
    de pago. Se añaden a los comprobantes de pago, los campos de cheque recibido
    y de pago indirecto. El campo de pago indirecto es un campo no visible, que
    se utilizará para registrar aquellos pagos que corresponden a documentos
    bancarios, es decir que no abonan directamente la factura sino que agrupan
    la deuda en un nuevo efecto cobrable."""
    _inherit = 'account.journal'
    _columns = {
         'indirect_payment': fields.boolean(
             'Gestión de efectos comerciales',
             help="Marcar si se va a utilizar este diario para registrar "
                  "apuntes de efectos correspondiente a gestión comercial "
                  "(pagarés, giros, cheques, etc). El sistema usuará la cuenta "
                  "definida en la ficha de cliente. Si está en blanco usuará "
                  "la definida en este diario"),
         'without_account_efect': fields.boolean(
             'Sin efecto contable',
             help="Si se marca esta opción, el sistema usará la cuenta de "
                  "cobrables/pagables del cliente en lugar de la cuenta de "
                  "efectos definidas en el diario o cliente"),
         'indirect_payment_type': fields.selection(
             [('documento', 'Documento de Cobro'),
              ('impago', 'Impagos'),
              ('incobrable', 'Incobrable')],
             'Tipo de Efecto Comercial', select=True),
		 'gestion_cobro': fields.boolean(
             'Gestión de cobro',
             help="Marque esta opción si el diario será utilizado para "
                  "operaciones de gestión de cobro"),
         'descuento_efectos': fields.boolean(
             'Descuento de Efectos',
             help="Marque esta opción si el diario será utilizado para "
                  "operaciones de- descuento de efectos"),
		 'property_account_descuento_efectos': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Cuenta de descuento de Efectos",
            method=True,
            view_load=True,
            required=False),
    }


class ResPartner(orm.Model):
    """Se añade campos a los partners para registrar las cuentas a utilizar
    para efectos comerciales"""
    _inherit = 'res.partner'

    _columns = {
        'property_account_efectos_cartera': fields.property(
            'account.account', type='many2one', relation='account.account',
            string="Efectos Comerciales en Cartera", method=True,
            view_load=True, domain="[('type', '=', 'receivable')]",
            help="Esta cuenta será utilizada en lugar de la cuenta por defecto "
                 "del diario para registrar los efectos comerciales en cartera",
            required=False),
        'property_account_impagos': fields.property(
            'account.account', type='many2one', relation='account.account',
            string="Impagos", method=True, view_load=True,
            domain="[('type', '=', 'receivable')]",
            help="Esta cuenta será utilizada en lugar de la cuenta por defecto "
                 "del diario para registrar los efectos impagados",
            required=False),
        'property_account_efectos_incobrables': fields.property(
            'account.account', type='many2one', relation='account.account',
            string="Incobrables", method=True, view_load=True,
            domain="[('type', '=', 'other')]",
            help="Esta cuenta será utilizada en lugar de la cuenta por defecto "
                 "para registrar los efectos incobrables", required=False),
    }


class AccountVoucher(orm.Model):
    """Se modifica la gestión de comprobantes de pago para que amplie la
    funcionalidad para registrar pagos mediante pagarés,cheques, etc..
    Se añaden a los comprobantes de pago, los campos de cheque recibido y de
    pago indirecto. El campo de pago indirecto es un campo no visible, que se
    utilizará para registrar aquellos pagos que corresponden a documentos
    bancarios, es decir que no abonan directamente la factura sino que agrupan
    la deuda en un nuevo efecto cobrable."""
    _inherit = 'account.voucher'

    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, amount,
                            currency_id, ttype, date, context=None):
        # We call the original event to give us back the original values
        res = super(AccountVoucher, self).onchange_partner_id(
            cr, uid, ids, partner_id, journal_id, amount, currency_id, type,
            date)
        if journal_id:
            journal_pool = self.pool['account.journal']
            journal = journal_pool.browse(cr, uid, journal_id, context=context)
            res['value']['indirect_payment'] = journal.indirect_payment
        return res

    def action_move_line_create(self, cr, uid, ids, context=None):
        def _get_payment_term_lines(term_id, amount):
            term_pool = self.pool['account.payment.term']
            if term_id and amount:
                terms = term_pool.compute(cr, uid, term_id, amount)
                return terms
            return False

        if context is None:
            context = {}
        move_pool = self.pool['account.move']
        move_line_pool = self.pool['account.move.line']
        currency_pool = self.pool['res.currency']
        tax_obj = self.pool['account.tax']
        seq_obj = self.pool['ir.sequence']
        for inv in self.browse(cr, uid, ids, context=context):
            if inv.move_id:
                continue
            context_multi_currency = context.copy()
            context_multi_currency.update({'date': inv.date})
            if inv.number:
                name = inv.number
            elif inv.journal_id.sequence_id:
                name = seq_obj.get_id(cr, uid, inv.journal_id.sequence_id.id)
            else:
                raise orm.except_orm(
                    _('Error !'),
                    _('Please define a sequence on the journal !'))
            if not inv.reference:
                ref = name.replace('/','')
            else:
                ref = inv.reference
            move = {
                'name': name,
                'journal_id': inv.journal_id.id,
                'narration': inv.narration,
                'date': inv.date,
                'ref': ref,
                'period_id': inv.period_id and inv.period_id.id or False
            }
            move_id = move_pool.create(cr, uid, move)
            # create the first line manually
            company_currency = inv.journal_id.company_id.currency_id.id
            current_currency = inv.currency_id.id
            debit = 0.0
            credit = 0.0
            # TODO: is there any other alternative then the voucher type ??
            # -for sale, purchase we have but for the payment and receipt we do
            # not have as based on the bank/cash journal we can not know its
            # payment or receipt
            if inv.type in ('purchase', 'payment'):
                credit = currency_pool.compute(
                    cr, uid, current_currency, company_currency, inv.amount,
                    context=context_multi_currency)
            elif inv.type in ('sale', 'receipt'):
                debit = currency_pool.compute(
                    cr, uid, current_currency, company_currency, inv.amount,
                    context=context_multi_currency)
            if debit < 0:
                credit = -debit
                debit = 0.0
            if credit < 0:
                debit = -credit
                credit = 0.0
            sign = debit - credit < 0 and -1 or 1
            # create the first line of the voucher
            # Lineas modificadas respecto al original
            cuenta_id = False
            if inv.journal_id.indirect_payment:
                if inv.journal_id.without_account_efect:
                    cuenta_id = inv.partner_id.property_account_receivable.id,
                else:
                    if inv.journal_id.indirect_payment_type == "documento":
                        partner = inv.partner_id
                        if partner.property_account_efectos_cartera.id:
                            cuenta_id = \
                                partner.property_account_efectos_cartera.id,
                        else:
                            cuenta_id = inv.account_id.id,
                    elif inv.journal_id.indirect_payment_type == "impago":
                        if partner.property_account_impagos.id:
                            cuenta_id = partner.property_account_impagos.id,
                        else:
                            cuenta_id = inv.account_id.id,
                    elif inv.journal_id.indirect_payment_type == "incobrable":
                        if partner.property_account_efectos_incobrables.id:
                            cuenta_id = \
                                partner.property_account_efectos_incobrables.id,
                        else:
                            cuenta_id = inv.account_id.id,
            else:
                cuenta_id = inv.account_id.id,
            move_line = {
                'name': inv.name or '/',
                'debit': debit,
                'credit': credit,
                'account_id': cuenta_id[0],
                'move_id': move_id,
                'journal_id': inv.journal_id.id,
                'period_id': inv.period_id.id,
                'partner_id': inv.partner_id.id,
                'currency_id': (company_currency != current_currency and
                                current_currency or company_currency),
                'amount_currency': (company_currency != current_currency and
                                    sign * inv.amount or 0.0),
                'date': inv.date,
                'date_maturity': inv.date_due
            }
            move_line_pool.create(cr, uid, move_line)
            rec_list_ids = []
            line_total = debit - credit
            if inv.type == 'sale':
                line_total = (line_total -
                              currency_pool.compute(
                                  cr, uid, inv.currency_id.id,
                                  company_currency, inv.tax_amount,
                                  context=context_multi_currency))
            elif inv.type == 'purchase':
                line_total = (line_total +
                              currency_pool.compute(
                                  cr, uid, inv.currency_id.id, company_currency,
                                  inv.tax_amount,
                                  context=context_multi_currency))
            for line in inv.line_ids:
                # create one move line per voucher line where amount is not 0.0
                if not line.amount:
                    continue
                # we check if the voucher line is fully paid or not and create
                # a move line to balance the payment and initial invoice if
                # needed
                if line.amount == line.amount_unreconciled:
                    # residual amount in company currency
                    amount = line.move_line_id.amount_residual
                else:
                    amount = currency_pool.compute(
                        cr, uid, current_currency, company_currency,
                        line.untax_amount or line.amount,
                        context=context_multi_currency)
                move_line = {
                    'journal_id': inv.journal_id.id,
                    'period_id': inv.period_id.id,
                    'name': line.name and line.name or '/',
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': inv.partner_id.id,
                    'currency_id': (company_currency != current_currency and
                                    current_currency or company_currency),
                    'analytic_account_id': line.account_analytic_id.id,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': 0.0,
                    'date': inv.date
                }
                if amount < 0:
                    amount = -amount
                    if line.type == 'dr':
                        line.type = 'cr'
                    else:
                        line.type = 'dr'
                if (line.type == 'dr'):
                    line_total += amount
                    move_line['debit'] = amount
                else:
                    line_total -= amount
                    move_line['credit'] = amount
                if inv.tax_id and inv.type in ('sale', 'purchase'):
                    move_line.update({
                        'account_tax_id': inv.tax_id.id,
                    })
                if move_line.get('account_tax_id', False):
                    tax_data = tax_obj.browse(
                        cr, uid, [move_line['account_tax_id']],
                        context=context)[0]
                    if not (tax_data.base_code_id and tax_data.tax_code_id):
                        raise orm.except_orm(
                            _('No Account Base Code and Account Tax Code!'),
                            _("You have to configure account base code and "
                              "account tax code on the '%s' tax!") %
                            (tax_data.name))
                sign = ((move_line['debit'] - move_line['credit']) < 0 and
                        -1 or 1)
                move_line['amount_currency'] = \
                    company_currency != current_currency and \
                    sign * line.amount or 0.0
                voucher_line = move_line_pool.create(cr, uid, move_line)
                if line.move_line_id.id:
                    rec_ids = [voucher_line, line.move_line_id.id]
                    rec_list_ids.append(rec_ids)
            if not currency_pool.is_zero(cr, uid, inv.currency_id, line_total):
                diff = line_total
                account_id = False
                if inv.payment_option == 'with_writeoff':
                    account_id = inv.writeoff_acc_id.id
                elif inv.type in ('sale', 'receipt'):
                    account_id = inv.partner_id.property_account_receivable.id
                else:
                    account_id = inv.partner_id.property_account_payable.id
                move_line = {
                    'name': name,
                    'account_id': account_id,
                    'move_id': move_id,
                    'partner_id': inv.partner_id.id,
                    'date': inv.date,
                    'credit': diff > 0 and diff or 0.0,
                    'debit': diff < 0 and -diff or 0.0,
                }
                move_line_pool.create(cr, uid, move_line)
            self.write(cr, uid, [inv.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            move_pool.post(cr, uid, [move_id], context={})
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    move_line_pool.reconcile_partial(cr, uid, rec_ids)
        return True

    _columns = {
         'payment_type': fields.many2one(
             'payment.type', 'Tipo de Pago',
             help="Tipo de pago establecido para el nuevo efecto a crear"),
         'received_check': fields.boolean(
             'Received check',
             help="To write down that a check in paper support has been "
                  "received, for example.", invisible=True),
         'indirect_payment': fields.boolean(
             'Document check', help="To mark if is not a direct payment"),
         'issued_check_ids':fields.one2many(
             'account.issued.check', 'voucher_id', 'Cheques emitidos'),
         'third_check_receipt_ids':fields.one2many(
             'account.third.check', 'voucher_id', 'Cheques de Terceros',
             required=False),
         'third_check_ids':fields.many2many(
             'account.third.check', 'third_check_voucher_rel', 'third_check_id',
             'voucher_id', 'Cheques de Terceros'),
         'property_account_gastos': fields.property(
             'account.account', type='many2one', relation='account.account',
             string="Cuenta Gastos", method=True, view_load=True,
             domain="[('type', '=', 'other')]",
             help="Gastos ocasionados por el impago", required=False),
         'expense_amount': fields.float('Cantidad Gastos'),
         'invoice_expense':fields.boolean('Facturar Gastos?'),
    }


class AccountMoveLine(orm.Model):
    """Se realizan los siguientes cambios....
    Se sobreescribe el campo funcional de tipo de pago con una nueva versión
    que hace lo mismo pero buscando además el valor del comprante de pago si
    el efecto no esta relacionado directamente con una factura.
    Se amplia el metodo original de account_payment_extension. Ahora si no
    encuentra el tipo de pago en la factura asociada el apunte, lo busca en el
    comprobante de pago... Si no está en ninguno de los dos, lo deja en blanco.
    """
    _inherit = 'account.move.line'

    def _get_move_lines_invoice(self, cr, uid, ids, context=None):
        result = set()
        invoice_obj = self.pool['account.invoice']
        for invoice in invoice_obj.browse(cr, uid, ids, context=context):
            if invoice.move_id:
                result.add(invoice.move_id.id)
        return list(result)

    def _get_move_lines_voucher(self, cr, uid, ids, context=None):
        result = set()
        voucher_obj = self.pool['account.voucher']
        for voucher in voucher_obj.browse(cr, uid, ids, context=context):
            if voucher.move_id:
                result.add(voucher.move_id.id)
        return list(result)

    def _payment_type_get(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        invoice_obj = self.pool['account.invoice']
        voucher_obj = self.pool['account.voucher']
        for rec in self.browse(cr, uid, ids, context):
            result[rec.id] = False
            invoice_id = invoice_obj.search(
                cr, uid, [('move_id', '=', rec.move_id.id)], context=context)
            if invoice_id:
                inv = invoice_obj.browse(cr, uid, invoice_id[0], context)
                if inv.payment_type:
                    result[rec.id] = inv.payment_type.id
            else:
                voucher_id = voucher_obj.search(
                    cr, uid, [('move_id', '=', rec.move_id.id)],
                    context=context)
                if voucher_id:
                    voucher = voucher_obj.browse(cr, uid, voucher_id[0],
                                                 context)
                    if voucher.payment_type:
                        result[rec.id] = voucher.payment_type.id
        return result

    def _indirect_payment_get(self, cr, uid, ids, field_name, arg,
                              context=None):
        """Se crea un nuevo campo funcional de tipo booleanto que obtiene si es
        pago corresponde a un efecto de gestión comercial o no."""
        result = {}
        voucher_obj = self.pool['account.voucher']
        for rec in self.browse(cr, uid, ids, context):
            result[rec.id] = False
            voucher_id = voucher_obj.search(
                cr, uid, [('move_id', '=', rec.move_id.id)], context=context)
            if voucher_id:
                voucher = voucher_obj.browse(cr, uid, voucher_id[0], context)
                if voucher.indirect_payment:
                    result[rec.id] = rec.debit > 0
        return result

    _columns = {
        'payment_type': fields.function(
            _payment_type_get, method=True, type="many2one",
            relation="payment.type", string="Payment type",
            store={
                'account.invoice': (_get_move_lines_invoice,
                                    ['payment_type'], 20),
                'account.voucher': (_get_move_lines_voucher,
                                    ['payment_type'], 20),
            }),
        'indirect_payment': fields.function(
            _indirect_payment_get, method=True, type="boolean",
            string="Indirect Payment",
            store={
                'account.voucher': (_get_move_lines_voucher,
                                    ['indirect_payment'], 20),
            })
    }
