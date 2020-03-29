# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
import re
from collections import OrderedDict
from odoo import models, fields, exceptions, _
from odoo.tools.misc import ustr

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    tbai_enabled = fields.Boolean(related='company_id.tbai_enabled', readonly=True)
    tbai_partner_idtype = fields.Selection(selection=[
        ('02', 'VAT identification number'),
        ('03', 'Passport'),
        ('04',
         'Official identification document issued by the country or territory of '
         'residence'),
        ('05', 'Residence certificate'),
        ('06', 'Other document')
    ], string='TicketBAI Identification Type Code', default='02')
    tbai_partner_identification_number = fields.Char(
        'TicketBAI Partner Identification Number',
        help="Used when the identification type code is not VAT identification number.")

    def tbai_get_partner_country_code(self):
        country_code, vat_number = \
            self.vat and self._split_vat(self.vat) or (None, None)
        if not ustr(country_code).encode('utf-8').isalpha():
            country_code = self.commercial_partner_id.country_id.code.upper()
        elif isinstance(country_code, str):
            country_code = country_code.upper()
        elif self.country_id:
            country_code = self.country_id.code
        return country_code

    def tbai_get_partner_vat_number(self):
        country_code, vat_number = \
            self.vat and self._split_vat(self.vat) or (None, None)
        if not ustr(country_code).encode('utf-8').isalpha():
            vat_number = self.vat
        return vat_number

    def tbai_build_id_destinatario(self):
        tax_agency = self.company_id.tbai_tax_agency_id
        res = OrderedDict({})
        nif = self.tbai_get_value_nif()
        if nif:
            res["NIF"] = nif
        else:
            id_otro = self.tbai_build_id_otro()
            if id_otro:
                res["IDOtro"] = id_otro
            else:
                raise exceptions.ValidationError(_(
                    "VAT number or another type of identification for %s is required!"
                ) % self.name)
        res[
            "ApellidosNombreRazonSocial"] = \
            self.tbai_get_value_apellidos_nombre_razon_social()

        codigo_postal = self.tbai_get_value_codigo_postal()
        if codigo_postal:
            res["CodigoPostal"] = codigo_postal
        elif tax_agency == self.env.ref("l10n_es_ticketbai.tbai_tax_agency_gipuzkoa"):
            raise exceptions.ValidationError(_(
                "Tax Agency %s requires Customer Zip code!") % tax_agency.name)
        direccion = self.tbai_get_value_direccion()
        if direccion:
            res["Direccion"] = direccion
        elif tax_agency == self.env.ref("l10n_es_ticketbai.tbai_tax_agency_gipuzkoa"):
            raise exceptions.ValidationError(_(
                "Tax Agency %s requires Customer Address!") % tax_agency.name)
        return res

    def tbai_build_id_otro(self):
        country_code = self.tbai_get_partner_country_code()
        if country_code and self.env.ref('base.es').code.upper() != country_code:
            res = OrderedDict({})
            codigo_pais = self.tbai_get_value_codigo_pais()
            if codigo_pais:
                res["CodigoPais"] = codigo_pais
            res["IDType"] = self.tbai_get_value_id_type()
            if self.tbai_partner_idtype and '02' != self.tbai_partner_idtype:
                res["ID"] = self.tbai_get_value_id()
            elif self.vat:
                res["ID"] = self.vat
            else:
                raise exceptions.ValidationError(_(
                    "VAT number or another type of identification for %s is required!"
                ) % self.name)
        else:
            res = {}
        return res

    def tbai_get_value_nif(self):
        """ V 1.1
        <element name="NIF" type="T:NIFType"/>
            <length value="9" />
            <pattern value="(([a-z|A-Z]{1}\\d{7}[a-z|A-Z]{1})|(\\d{8}[a-z|A-Z]{1})|
            ([a-z|A-Z]{1}\\d{8}))" />
        :return: VAT Number for Customers from Spain or the Company associated partner.
        """
        country_code = self.tbai_get_partner_country_code()
        vat_number = self.tbai_get_partner_vat_number()
        if vat_number and country_code and \
                self.env.ref('base.es').code.upper() == country_code:
            pattern = r"(([a-z|A-Z]{1}\d{7}[a-z|A-Z]{1})|(\d{8}[a-z|A-Z]{1})|" \
                      r"([a-z|A-Z]{1}\d{8}))"
            match_res = re.match(pattern, vat_number)
            if not match_res or (
                    match_res and match_res.group(0) != vat_number) or 9 != len(
                    vat_number):
                raise exceptions.ValidationError(_(
                    "Invalid VAT number format for %s!") % self.name)
            res = vat_number
        else:
            res = ''
        return res

    def tbai_get_value_apellidos_nombre_razon_social(self):
        """ V 1.1
        <element name="ApellidosNombreRazonSocial" type="T:TextMax120Type"/>
            <maxLength value="120"/>
        :return: Name and surname, or business name
        """
        if 120 < len(self.name.strip()):
            raise exceptions.ValidationError(_(
                "Name %s too long. Should be 120 characters max.!") % self.name)
        return self.name.strip()  # Remove leading and trailing whitespace

    def tbai_get_value_codigo_pais(self):
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
        if country_code and self.tbai_partner_idtype and '02' != \
                self.tbai_partner_idtype:
            res = country_code
        return res

    def tbai_get_value_id_type(self):
        """ V 1.1
        <element name="IDType" type="T:IDTypeType"/>
        :return: Identification Type Code
        """
        if self.tbai_partner_idtype:
            res = self.tbai_partner_idtype
        else:
            raise exceptions.ValidationError(_(
                "Identification type code required for %s") % self.name)
        return res

    def tbai_get_value_id(self):
        """ V 1.1
        <element name="ID" type="T:TextMax20Type"/>
            <maxLength value="20"/>
        :return: Identification Number
        """
        if self.tbai_partner_identification_number:
            if 20 < len(self.tbai_partner_identification_number):
                raise exceptions.ValidationError(_(
                    "Invalid TicketBAI Partner Identification Number format for %s. "
                    "Should be 20 characters max.!"
                ) % self.name)
        else:
            raise exceptions.ValidationError(_(
                "TicketBAI Partner Identification Number for %s should not be empty!"
            ) % self.name)
        return self.tbai_partner_identification_number

    def tbai_get_value_codigo_postal(self):
        """ V 1.2
        <element name="CodigoPostal" type="T:TextMax20Type" minOccurs="0"/>
            <maxLength value="20"/>
        :return: ZIP Code
        """
        if self.zip and 20 < len(self.zip):
            raise exceptions.ValidationError(_(
                "Invalid Zip code format for %s. Should be 20 characters max.!"
            ) % self.name)
        return self.zip

    def tbai_get_value_direccion(self):
        """ V 1.2
        <element name="Direccion" type="T:TextMax250Type" minOccurs="0"/>
            <maxLength value="250"/>
        """
        address_fields = [
            "%s" % (self.street or ''),
            "%s" % (self.street2 or ''),
            ("%s %s" % (self.zip or '', self.city or '')).strip(),
            "%s" % (self.state_id.name or ''),
            "%s" % (self.country_id.name or '')
        ]
        contact_address = ', '.join([x for x in address_fields if x])
        if contact_address and 250 < len(contact_address):
            _logger.exception(contact_address)
            raise exceptions.ValidationError(_(
                "Invalid Complete Address format for %s. Should be 250 characters max.!"
            ) % self.name)
        return contact_address
