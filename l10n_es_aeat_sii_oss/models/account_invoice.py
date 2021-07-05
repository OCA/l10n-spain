# -*- coding: utf-8 -*-
# Copyright 2021 FactorLibre - Rodrigo Bonilla <rodrigo.bonilla@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _get_sii_taxes_map(self, codes):
        """Return the codes that correspond to that sii map line codes.

        :param self: Single invoice record.
        :param codes: List of code strings to get the mapping.
        :return: Recordset with the corresponding codes
        """
        taxes = super(AccountInvoice, self)._get_sii_taxes_map(codes)
        if any([x for x in codes if x in ['SFENS', 'NotIncludedInTotal']]):
            taxes |= self.env['account.tax'].search([
                ('oss_country_id', '!=', False),
                ('company_id', '=', self.company_id.id), ])
        return taxes
