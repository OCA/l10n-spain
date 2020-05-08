# -*- coding: utf-8 -*-
# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from odoo import models, fields
from odoo.tools.misc import ustr

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    tbai_enabled = fields.Boolean(related='company_id.tbai_enabled', readonly=True)
    tbai_partner_idtype = fields.Selection(selection=[
        ('02', 'VAT identification number'),
        ('03', 'Passport'),
        ('04', 'Official identification document issued by the country or territory of residence'),
        ('05', 'Residence certificate'),
        ('06', 'Other document')
    ], string='TicketBAI Identification Type Code', default='02')

    def tbai_get_partner_country_code(self):
        country_code, vat_number = self.vat and self._split_vat(self.vat) or (None, None)
        if not ustr(country_code).encode('utf-8').isalpha():
            country_code = self.commercial_partner_id.country_id.code.upper()
        elif country_code is not None:
            country_code = country_code.upper()
        return country_code

    def tbai_get_partner_vat_number(self):
        country_code, vat_number = self.vat and self._split_vat(self.vat) or (None, None)
        if not ustr(country_code).encode('utf-8').isalpha():
            vat_number = self.vat
        return vat_number

    def tbai_get_context_records_IDDestinatario(self):
        return self

    def tbai_get_context_records_IDOtro(self):
        country_code = self.tbai_get_partner_country_code()
        if country_code and self.env.ref('base.es').code.upper() != country_code:
            res = self
        else:
            res = None
        return res

    def tbai_get_value_NIF(self, **kwargs):
        """ V 1.1
        <element name="NIF" type="T:NIFType"/>
            <length value="9" />
            <pattern value="(([a-z|A-Z]{1}\d{7}[a-z|A-Z]{1})|(\d{8}[a-z|A-Z]{1})|([a-z|A-Z]{1}\d{8}))" />
        :return: VAT Number for Customers from Spain or the Company associated partner.
        """
        country_code = self.tbai_get_partner_country_code()
        vat_number = self.tbai_get_partner_vat_number()
        if country_code and self.env.ref('base.es').code.upper() == country_code:
            res = vat_number
        else:
            res = ''
        return res

    def tbai_get_value_ApellidosNombreRazonSocial(self, max_length=None, **kwargs):
        """ V 1.1
        <element name="ApellidosNombreRazonSocial" type="T:TextMax120Type"/>
            <maxLength value="120"/>
        :return: Name and surname, or business name
        """
        return self.name[:max_length].strip()  # Remove leading and trailing whitespace

    def tbai_get_value_CodigoPais(self, **kwargs):
        """ V 1.1
        <element name="CodigoPais" type="T:CountryType2" minOccurs="0"/>
            [
                <enumeration value="AF"/>
                ...
            ]
        :return: Country code
        """
        res = ''
        country_code = self.tbai_get_partner_country_code()
        if country_code and self.env.ref('base.es').code.upper() != country_code and self.tbai_partner_idtype and \
                '02' != self.tbai_partner_idtype:
            res = country_code
        return res

    def tbai_get_value_IDType(self, **kwargs):
        """ V 1.1
        <element name="IDType" type="T:IDTypeType"/>
        :return: Identification Type Code
        """
        country_code = self.tbai_get_partner_country_code()
        if country_code and self.env.ref('base.es').code.upper() != country_code:
            res = self.tbai_partner_idtype
        else:
            res = ''
        return res

    def tbai_get_value_ID(self, **kwargs):
        """ V 1.1
        <element name="ID" type="T:TextMax20Type"/>
            <maxLength value="20"/>
        :return: Identification Number
        """
        country_code = self.tbai_get_partner_country_code()
        if country_code and self.env.ref('base.es').code.upper() != country_code:
            res = self.tbai_get_partner_vat_number()
        else:
            res = ''
        return res

    def tbai_get_value_CodigoPostal(self, **kwargs):
        """ V 1.1
        <element name="CodigoPostal" type="T:CodigoPostalType" minOccurs="0"/>
            <length value="5"/>
            <pattern value="[0-9]*"></pattern>
        :return: ZIP Code
        """
        # Not all countries comply with a length of 5 characters
        country_code = self.tbai_get_partner_country_code()
        if country_code and self.env.ref('base.es').code.upper() == country_code and self.zip:
            res = self.zip
        else:
            res = ''
        return res
