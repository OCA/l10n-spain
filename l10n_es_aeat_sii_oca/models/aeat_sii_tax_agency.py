# -*- coding: utf-8 -*-
# Copyright 2018 Javi Melendez <javimelex@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class AeatSiiTaxAgency(models.Model):
    _name = 'aeat.sii.tax.agency'
    _description = 'Aeat SII Tax Agency'

    name = fields.Char(string='Tax Agency', required=True)
    wsdl_out = fields.Char(
        string='SuministroFactEmitidas WSDL', required=True)
    wsdl_out_test_address = fields.Char(
        string='SuministroFactEmitidas Test Address')
    wsdl_in = fields.Char(
        string='SuministroFactRecibidas WSDL', required=True)
    wsdl_in_test_address = fields.Char(
        string='SuministroFactRecibidas Test Address')
    wsdl_pi = fields.Char(
        string='SuministroBienesInversion WSDL', required=True)
    wsdl_pi_test_address = fields.Char(
        string='SuministroBienesInversion Test Address')
    wsdl_ic = fields.Char(
        string='SuministroOpIntracomunitarias WSDL', required=True)
    wsdl_ic_test_address = fields.Char(
        string='SuministroOpIntracomunitarias Test Address')
    wsdl_pr = fields.Char(
        string='SuministroCobrosEmitidas WSDL', required=True)
    wsdl_pr_test_address = fields.Char(
        string='SuministroCobrosEmitidas Test Address')
    wsdl_ott = fields.Char(
        string='SuministroOpTrascendTribu WSDL', required=True)
    wsdl_ott_test_address = fields.Char(
        string='SuministroOpTrascendTribu Test Address')
    wsdl_ps = fields.Char(
        string='SuministroPagosRecibidas WSDL', required=True)
    wsdl_ps_test_address = fields.Char(
        string='SuministroPagosRecibidas Test Address')

    @api.multi
    def _connect_params_sii(self, mapping_key, company):
        self.ensure_one()
        wsdl_key = self.env['account.invoice'].SII_WDSL_MAPPING[mapping_key]
        wsdl_field = wsdl_key.split('.')[1]
        wsdl_test_field = wsdl_field + '_test_address'
        return {
            'wsdl': getattr(self, wsdl_field),
            'address': (
                getattr(self, wsdl_test_field) if company.sii_test
                else False
            ),
        }
