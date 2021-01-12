# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from collections import OrderedDict
from odoo import release, models, fields, api, exceptions, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    tbai_enabled = fields.Boolean('Enable TicketBAI', copy=False)
    tbai_test_enabled = fields.Boolean('Enable testing', copy=False)
    tbai_license_key = fields.Char('License Key', copy=False)
    tbai_developer_id = fields.Many2one(
        comodel_name='res.partner', string='Developer', copy=False)
    tbai_software_name = fields.Char(
        string='Software Name', help="Registered name at the Tax Agency.", copy=False)
    tbai_device_serial_number = fields.Char('Device Serial Number', copy=False)
    tbai_tax_agency_id = fields.Many2one(
        comodel_name='tbai.tax.agency', string='Tax Agency', copy=False)
    tbai_vat_regime_simplified = fields.Boolean('Regime Simplified', copy=False)
    tbai_certificate_id = fields.Many2one(
        comodel_name='l10n.es.aeat.certificate', string='Certificate',
        domain="[('state', '=', 'active'), ('company_id', '=', id)]", copy=False)
    tbai_last_invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Last Invoice', copy=False)

    @api.onchange('tbai_enabled')
    def onchange_tbai_enabled(self):
        if not self.tbai_enabled:
            self.tbai_license_key = ''
            self.tbai_developer_id = False
            self.tbai_software_name = ''
            self.tbai_device_serial_number = ''
            self.tbai_tax_agency_id = False
            self.tbai_vat_regime_simplified = False
            self.tbai_certificate_id = False

    def tbai_build_software(self):
        return OrderedDict([
            ("LicenciaTBAI", self.tbai_get_value_licencia_tbai()),
            ("EntidadDesarrolladora", self.tbai_build_entidad_desarrolladora()),
            ("Nombre", self.tbai_get_value_nombre()),
            ("Version", self.tbai_get_value_version())
        ])

    def tbai_build_entidad_desarrolladora(self):
        res = OrderedDict({})
        nif = self.tbai_developer_id.tbai_get_value_nif()
        if nif:
            res["NIF"] = nif
        else:
            id_otro = self.tbai_developer_id.tbai_build_id_otro()
            if id_otro:
                res["IDOtro"] = id_otro
            else:
                raise exceptions.ValidationError(_(
                    "VAT number or another type of identification for %s is required!"
                ) % self.tbai_developer_id.name)
        return res

    def tbai_get_value_licencia_tbai(self):
        """ V 1.1
        <element name="LicenciaTBAI" type="T:TextMax20Type"/>
            <maxLength value="20"/>
        :return: TicketBAI Developer License Key
        """
        if not self.tbai_license_key:
            raise exceptions.ValidationError(_(
                "TicketBAI License Key for company %s should not be empty!"
            ) % self.name)
        if 20 < len(self.tbai_license_key):
            raise exceptions.ValidationError(_(
                "TicketBAI License Key for company %s should be 20 characters max.!"
            ) % self.name)
        return self.tbai_license_key

    def tbai_get_value_nombre(self):
        """ V 1.1
        <element name="Nombre" type="T:TextMax120Type"/>
            <maxLength value="120"/>
        :return: Software Name
        """
        return self.tbai_software_name

    def tbai_get_value_version(self):
        """ V 1.1
        <element name="Version" type="T:TextMax20Type"/>
            <maxLength value="20"/>
        :return: Software Version
        """
        return release.version

    def tbai_get_value_num_serie_dispositivo(self):
        """ V 1.1
        <element name="NumSerieDispositivo" type="T:TextMax30Type" minOccurs="0"/>
            <maxLength value="30"/>
        :return: Device Serial Number
        """
        res = self.tbai_device_serial_number
        if res and 30 < len(res):
            raise exceptions.ValidationError(_(
                "Company %s Device Serial Number longer than expected, 30 characters "
                "max!") % self.name)
        return res
