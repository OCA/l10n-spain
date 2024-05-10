# Copyright 2024 Aures Tic - Jose Zambudio <jose@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

VERIFACTU_WDSL_MAPPING = {
    "out_invoice": "verifactu_wsdl_out",
    "out_refund": "verifactu_wsdl_out",
}
VERIFACTU_PORT_NAME_MAPPING = {
    "out_invoice": "SuministroInformacion",
    "out_refund": "SuministroInformacion",
}


class AeatTaxAgency(models.Model):
    _inherit = "aeat.tax.agency"

    verifactu_wsdl_out = fields.Char(string="SuministroInformacion WSDL")
    verifactu_wsdl_out_test_address = fields.Char(
        string="SuministroInformacion Test Address"
    )

    def _connect_params_verifactu(self, mapping_key, company):
        self.ensure_one()
        wsdl_field = VERIFACTU_WDSL_MAPPING[mapping_key]
        wsdl_test_field = wsdl_field + "_test_address"
        port_name = VERIFACTU_PORT_NAME_MAPPING[mapping_key]
        address = getattr(self, wsdl_test_field) if company.verifactu_test else False
        if not address and company.verifactu_test:
            # If not test address is provides we try to get it using the port name.
            port_name += "Pruebas"
        return {
            "wsdl": getattr(self, wsdl_field),
            "address": address,
            "port_name": port_name,
        }
