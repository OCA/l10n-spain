# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    def tbai_is_subject_to_tax(self):
        s_iva_ns_descriptions = \
            self.env.ref('l10n_es_ticketbai.tbai_tax_map_SNS').tax_template_ids.mapped(
                'description')
        s_iva_ns_b_descriptions = \
            self.env.ref('l10n_es_ticketbai.tbai_tax_map_BNS').tax_template_ids.mapped(
                'description')
        return self.description not in s_iva_ns_descriptions + s_iva_ns_b_descriptions

    def tbai_is_tax_exempted(self):
        return self.tax_group_id.id == self.env.ref('l10n_es.tax_group_iva_0').id

    def tbai_is_not_tax_exempted(self):
        return self.tax_group_id.id != self.env.ref('l10n_es.tax_group_iva_0').id
