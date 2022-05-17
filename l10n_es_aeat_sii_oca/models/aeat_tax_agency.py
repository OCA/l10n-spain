# Copyright 2018 Javi Melendez <javimelex@gmail.com>
# Copyright 2022 Lois Rilo <lois.rilo@forgeflow.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

SII_WDSL_MAPPING = {
    "out_invoice": "sii_wsdl_out",
    "out_refund": "sii_wsdl_out",
    "in_invoice": "sii_wsdl_in",
    "in_refund": "sii_wsdl_in",
}
SII_PORT_NAME_MAPPING = {
    "out_invoice": "SuministroFactEmitidas",
    "out_refund": "SuministroFactEmitidas",
    "in_invoice": "SuministroFactRecibidas",
    "in_refund": "SuministroFactRecibidas",
}


class AeatTaxAgency(models.Model):
    _inherit = "aeat.tax.agency"

    sii_wsdl_out = fields.Char(string="SuministroFactEmitidas WSDL")
    sii_wsdl_out_test_address = fields.Char(
        string="SuministroFactEmitidas Test Address"
    )
    sii_wsdl_in = fields.Char(string="SuministroFactRecibidas WSDL")
    sii_wsdl_in_test_address = fields.Char(
        string="SuministroFactRecibidas Test Address"
    )
    sii_wsdl_pi = fields.Char(string="SuministroBienesInversion WSDL")
    sii_wsdl_pi_test_address = fields.Char(
        string="SuministroBienesInversion Test Address"
    )
    sii_wsdl_ic = fields.Char(string="SuministroOpIntracomunitarias WSDL")
    sii_wsdl_ic_test_address = fields.Char(
        string="SuministroOpIntracomunitarias Test Address"
    )
    sii_wsdl_pr = fields.Char(string="SuministroCobrosEmitidas WSDL")
    sii_wsdl_pr_test_address = fields.Char(
        string="SuministroCobrosEmitidas Test Address"
    )
    sii_wsdl_ott = fields.Char(string="SuministroOpTrascendTribu WSDL")
    sii_wsdl_ott_test_address = fields.Char(
        string="SuministroOpTrascendTribu Test Address"
    )
    sii_wsdl_ps = fields.Char(string="SuministroPagosRecibidas WSDL")
    sii_wsdl_ps_test_address = fields.Char(
        string="SuministroPagosRecibidas Test Address"
    )

    def _connect_params_sii(self, mapping_key, company):
        self.ensure_one()
        wsdl_field = SII_WDSL_MAPPING[mapping_key]
        wsdl_test_field = wsdl_field + "_test_address"
        port_name = SII_PORT_NAME_MAPPING[mapping_key]
        address = getattr(self, wsdl_test_field) if company.sii_test else False
        if not address and company.sii_test:
            # If not test address is provides we try to get it using the port name.
            port_name += "Pruebas"
        return {
            "wsdl": getattr(self, wsdl_field),
            "address": address,
            "port_name": port_name,
        }
