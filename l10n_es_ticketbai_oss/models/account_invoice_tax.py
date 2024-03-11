# Copyright 2024 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountInvoiceTax(models.Model):
    _inherit = "account.invoice.tax"

    def tbai_es_prestacion_servicios(self):
        if self.tax_id.tbai_tax_map_id:
            return (
                True
                if self.tax_id.tbai_tax_map_id.code in ("SNS", "SIE", "S", "SER")
                else False
            )
        return super().tbai_es_prestacion_servicios()

    def tbai_es_entrega(self):
        if self.tax_id.tbai_tax_map_id:
            return (
                True
                if self.tax_id.tbai_tax_map_id.code in ("B", "BNS", "IEE", "SER")
                else False
            )
        return super().tbai_es_entrega()

    def tbai_get_value_causa(self):
        if self.tax_id.not_subject_to_cause:
            return self.tax_id.not_subject_to_cause
        return super().tbai_get_value_causa()
