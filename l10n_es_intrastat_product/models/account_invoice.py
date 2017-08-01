# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    # use 'res.country.state' i.s.o. 'intrastat.region'
    src_dest_state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='Origin/Destination State',
        default=lambda self: self._default_src_dest_state_id(),
        help="Origin/Destination Region."
             "\nThis field is used for the Intrastat Declaration."
             "For a customer invoice, contains Spain's state "
             "number from which the goods have be shipped. "
             "For a supplier invoice, contains Spain's state number "
             "of reception of the goods",
        ondelete='restrict')

    @api.model
    def _default_src_dest_state_id(self):
        rco = self.env['res.company']
        company_id = rco._company_default_get('account.invoice')
        company = rco.browse(company_id)
        return company.intrastat_state_id

    @api.model
    def _default_intrastat_transaction_id(self):
        transaction = super(
            AccountInvoice, self)._default_intrastat_transaction_id()
        if not transaction:
            cpy_id = self.env[
                'res.company']._company_default_get('account.invoice')
            cpy = self.env['res.company'].browse(cpy_id)
            if cpy.country_id.code.lower() == 'es':
                module = __name__.split('addons.')[1].split('.')[0]
                transaction = self.env.ref(
                    '%s.intrastat_transaction_1' % module)
        return transaction
