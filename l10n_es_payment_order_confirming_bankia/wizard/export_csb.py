# -*- coding: utf-8 -*-
# (c) 2016 Soluntec Proyectos y Soluciones TIC. - Rubén Francés , Nacho Torró
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openerp import models, api
from .confirming_bankia import ConfirmingBankia


class BankingExportCsbWizard(models.TransientModel):
    _inherit = 'banking.export.csb.wizard'

    @api.model
    def _check_company_bank_account(self, payment_order):
        """Don't make this check for Confirming Bankia."""
        if not payment_order.mode.is_conf_bankia:
            super(BankingExportCsbWizard, self)._check_company_bank_account(
                payment_order)

    @api.model
    def _check_required_bank_account(self, payment_order, pay_lines):
        """Don't make this check for Confirming Bankia."""
        if not payment_order.mode.is_conf_bankia:
            super(BankingExportCsbWizard, self)._check_required_bank_account(
                payment_order, pay_lines)

    @api.model
    def _get_csb_exporter(self, payment_order):
        if payment_order.mode.type.code == 'conf_bankia':
            csb = ConfirmingBankia(self.env)
        else:
            csb = super(BankingExportCsbWizard, self)._get_csb_exporter(
                payment_order)
        return csb
