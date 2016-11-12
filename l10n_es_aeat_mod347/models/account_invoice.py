# -*- coding: utf-8 -*-
# © 2004-2011 Pexego Sistemas Informáticos. (http://pexego.es)
# © 2012 NaN·Tic  (http://www.nan-tic.com)
# © 2013 Acysos (http://www.acysos.com)
# © 2013 Joaquín Pedrosa Gutierrez (http://gutierrezweb.es)
# © 2014-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
#             (http://www.serviciosbaeza.com)
# © 2016 Antiun Ingenieria S.L. - Antonio Espinosa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    @api.depends('cc_amount_untaxed',
                 'tax_line', 'tax_line.amount')
    def _compute_amount_total_wo_irpf(self):
        for invoice in self:
            invoice.amount_total_wo_irpf = invoice.cc_amount_untaxed
            for tax_line in invoice.tax_line:
                if 'IRPF' not in tax_line.name:
                    invoice.amount_total_wo_irpf += tax_line.amount

    amount_total_wo_irpf = fields.Float(
        compute="_compute_amount_total_wo_irpf", store=True, readonly=True,
        string="Total amount without IRPF taxes")
    not_in_mod347 = fields.Boolean(
        "Not included in 347 report",
        help="If you mark this field, this invoice will not be included in "
             "any AEAT 347 model report.", default=False)
