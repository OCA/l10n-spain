# -*- coding: utf-8 -*-
# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import release, models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    tbai_enabled = fields.Boolean('Enable TicketBAI')
    tbai_test_mode = fields.Boolean('Test Mode')
    tbai_license_key = fields.Char('License Key')
    tbai_developer_id = fields.Many2one(comodel_name='res.partner', string='Developer')
    tbai_device_serial_number = fields.Char('Device Serial Number')
    tbai_tax_agency_id = fields.Many2one(comodel_name='tbai.tax.agency', string='TicketBAI Tax Agency')
    tbai_vat_regime_simplified = fields.Boolean('Regime Simplified')
    tbai_aeat_certificate_id = fields.Many2one(
        comodel_name='l10n.es.aeat.certificate', string='Certificate',
        domain="[('state', '=', 'active'), ('company_id', '=', id)]")

    @api.onchange('tbai_enabled')
    def onchange_tbai_enabled(self):
        if not self.tbai_enabled:
            self.tbai_test_mode = False
            self.tbai_license_key = ''
            self.tbai_developer_id = False
            self.tbai_device_serial_number = ''
            self.tbai_tax_agency_id = False
            self.tbai_vat_regime_simplified = False
            self.tbai_aeat_certificate_id = False

    def tbai_get_context_records_EntidadDesarrolladora(self):
        return self.tbai_developer_id

    def tbai_get_value_LicenciaTBAI(self, **kwargs):
        """ V 1.1
        <element name="LicenciaTBAI" type="T:TextMax20Type"/>
            <maxLength value="20"/>
        :return: TicketBAI Developer License Key
        """
        return self.tbai_license_key

    def tbai_get_value_Nombre(self, **kwargs):
        """ V 1.1
        <element name="Nombre" type="T:TextMax120Type"/>
            <maxLength value="120"/>
        :return: Software Name
        """
        return release.product_name

    def tbai_get_value_Version(self, **kwargs):
        """ V 1.1
        <element name="Version" type="T:TextMax20Type"/>
            <maxLength value="20"/>
        :return: Software Version
        """
        return release.version
