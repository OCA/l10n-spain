# Copyright 2024 Aures Tic - Jose Zambudio <jose@aurestic.es>
# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AeatTaxAgency(models.Model):
    _inherit = "aeat.tax.agency"

    verifactu_wsdl_out = fields.Char(string="VERI*FACTU WSDL")
    verifactu_wsdl_out_test_address = fields.Char(string="VERI*FACTU Test Address")
    verifactu_qr_base_url = fields.Char(string="VERI*FACTU QR Base URL")
    verifactu_qr_base_url_test_address = fields.Char(
        string="VERI*FACTU QR Base URL Test"
    )

    def _connect_params_verifactu(self, company):
        self.ensure_one()
        wsdl_field = "verifactu_wsdl_out"
        wsdl_test_field = wsdl_field + "_test_address"
        port_name = "SistemaVerifactu"
        address = self[wsdl_test_field] if company.verifactu_test else False
        if not address and company.verifactu_test:
            port_name += "Pruebas"
        return {
            "wsdl": self[wsdl_field],
            "address": address,
            "port_name": port_name,
        }
