# Copyright 2022 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    has_equivalence_surcharge = fields.Boolean(
        string='Has Equivalence Surcharge',
        default=True)
    is_equivalence_surcharge = fields.Boolean(
        compute='_compute_product_equivalence_surcharge')

    @api.depends('company_id.partner_id.property_account_position_id')
    def _compute_product_equivalence_surcharge(self):
        self.is_equivalence_surcharge = True \
            if self.company_id.tbai_vat_regime.id in \
            [self.env.ref("l10n_es_ticketbai.tbai_vat_regime_51").id,
             self.env.ref("l10n_es_ticketbai.tbai_vat_regime_52").id]\
            else False
