# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2016 Factor Libre S.L. (http://factorlibre.com)
#                       Kiko Peiro <francisco.peiro@factorlibre.com>
#
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

import logging

from openerp import api, models


_logger = logging.getLogger(__name__)


class L10nEsAeatMod340CashBasisCalculateRecords(models.TransientModel):
    _inherit = "l10n.es.aeat.mod340.calculate_records"

    @api.multi
    def _calculate_records(self, recalculate=True):

        invoice_obj = self.env['account.invoice']
        invoices340 = self.env['l10n.es.aeat.mod340.issued']
        invoices340_rec = self.env['l10n.es.aeat.mod340.received']
        report = self.env['l10n.es.aeat.mod340.report']

        for record in self:
            super(L10nEsAeatMod340CashBasisCalculateRecords, record).\
                _calculate_records(recalculate=recalculate)
            mod340 = report.browse(record.id)
            account_period_ids = [x.id for x in mod340.periods]
            domain = [
                ('period_id', 'in', account_period_ids),
                ('state', 'in', ('open', 'paid')),
                ('vat_on_payment', '=', True)
            ]

            invoice_ids = invoice_obj.search(domain)
            for invoice in invoice_ids:
                domain_records = [
                    ('mod340_id', '=', record.id),
                    ('invoice_id', '=', invoice.id)
                ]
                invoice_created_id = False
                if invoice.type in ['out_invoice', 'out_refund']:
                    invoice_created_id = invoices340.search(domain_records)
                if invoice.type in ['in_invoice', 'in_refund']:
                    invoice_created_id = invoices340_rec.search(domain_records)
                if invoice_created_id:
                    invoice_created_id = invoice_created_id[0]
                    date_payment = False
                    payment_amount = 0
                    name_payment_method = ''
                    for payment_id in\
                            invoice_created_id.invoice_id.payment_ids:
                        if not date_payment:
                            date_payment = payment_id.date
                        if not name_payment_method:
                            name_payment_method_id = self.env[
                                'res.partner.bank'].search(
                                [('journal_id', '=', payment_id.journal_id.id)]
                            )
                            if name_payment_method_id:
                                name_payment_method =\
                                    name_payment_method_id[0].\
                                    acc_number.replace(' ', '')
                        payment_amount = payment_amount + payment_id.debit

                    invoice_created_id.write({
                        'date_payment': date_payment,
                        'payment_amount': payment_amount,
                        'name_payment_method': name_payment_method,
                        'key_operation': 'Z'
                    })
        return True
