# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from ..utils import utils as tbai_utils
from odoo import models, fields, exceptions, api, _
from odoo.tools.misc import ustr
from .res_country import CountryCode


class TicketBaiCustomerIdType(tbai_utils.EnumValues):
    T02 = '02'
    T03 = '03'
    T04 = '04'
    T05 = '05'
    T06 = '06'


class ResPartner(models.Model):
    _inherit = 'res.partner'

    tbai_enabled = fields.Boolean(related='company_id.tbai_enabled', readonly=True)
    tbai_partner_idtype = fields.Selection(selection=[
        (TicketBaiCustomerIdType.T02.value, 'VAT identification number'),
        (TicketBaiCustomerIdType.T03.value, 'Passport'),
        (TicketBaiCustomerIdType.T04.value,
         'Official identification document issued by the country or territory of '
         'residence'),
        (TicketBaiCustomerIdType.T05.value, 'Residence certificate'),
        (TicketBaiCustomerIdType.T06.value, 'Other document')
    ], string='TicketBAI Identification Type Code',
        default=TicketBaiCustomerIdType.T02.value)

    @api.multi
    @api.constrains('vat', 'tbai_partner_idtype')
    def check_vat(self):
        for partner in self:
            if partner.tbai_partner_idtype == '02':
                super().check_vat()
            else:
                if 20 < len(partner.vat):
                    raise exceptions.ValidationError(_(
                        "Partner Identification Number %s longer than expected. "
                        "Should be 20 characters max.!"
                    ) % partner.name)

    @api.multi
    @api.constrains('tbai_partner_idtype')
    def _check_idtype(self):
        for partner in self:
            if self.country_id.code == CountryCode.ES.value \
                    and partner.tbai_partner_idtype not in ('02', '03'):
                raise exceptions.ValidationError(_(
                    "Identification type can only be NIF or Passport for "
                    "Spanish partners."
                ))

    def get_identification_number(self):
        for partner in self:
            if partner.vat and partner.tbai_partner_idtype == '02':
                nif_value = partner.tbai_get_value_nif()
                if nif_value:
                    return nif_value
                elif not partner.vat.startswith(partner.country_id.code):
                    return partner.country_id.code + partner.vat
            else:
                return partner.vat

    def is_spanish_nif(self):
        self.ensure_one()
        if not self.vat:
            raise exceptions.ValidationError(_(
                "TicketBAI Invoice %s: Identification Number is required!"
            ) % (self.name))
        is_spanish = True
        if not self.country_id.code == CountryCode.ES.value:
            is_spanish = False
        else:
            try:
                tbai_utils.check_spanish_vat_number(_(
                    "TicketBAI Invoice: Customer %s identification number"
                ) % (self.name), self.get_identification_number())
            except exceptions.ValidationError:
                is_spanish = False
        return is_spanish

    def is_spanish_vat_breakdown(self):
        self.ensure_one()
        is_spanish_vat_breakdown = False
        if self.tbai_partner_idtype == '02' \
                and self.country_id.code == self.env.ref('base.es').code.upper() \
                and not self.vat.startswith('N'):
            is_spanish_vat_breakdown = True
        return is_spanish_vat_breakdown

    def _check_recipient_country(self):
        self.ensure_one()
        if self.country_id.code not in CountryCode.values():
            raise exceptions.ValidationError(_(
                "TicketBAI Invoice %s: Customer %s Country Code %s not valid."
            ) % (self.name, self.name, self.country_id.code))

    def _check_recipient_zip(self):
        self.ensure_one()
        if self.zip and 20 < len(self.zip):
            raise exceptions.ValidationError(_(
                "TicketBAI Invoice %s:\n"
                "Customer %s ZIP Code %s longer than expected. "
                "Should be 20 characters max.!"
            ) % (self.name, self.name, self.zip))

    def _check_recipient_address(self):
        self.ensure_one()
        address = self.tbai_get_value_direccion()
        if address and 250 < len(address):
            raise exceptions.ValidationError(_(
                "TicketBAI Invoice %s:\n"
                "Customer %s Address %s longer than expected. "
                "Should be 250 characters max.!"
            ) % (self.name, self.name, address))

    @api.multi
    def check_recipient_data(self):
        for record in self:
            record._check_recipient_country()
            record._check_recipient_zip()
            record._check_recipient_address()

    def tbai_get_partner_country_code(self):
        self.ensure_one()
        country_code, vat_number = \
            self.vat and tbai_utils.split_vat(self.vat) or (None, None)
        if not ustr(country_code).encode('utf-8').isalpha():
            country_code = self.commercial_partner_id.country_id.code
        elif isinstance(country_code, str):
            country_code = country_code
        elif self.country_id:
            country_code = self.country_id.code
        if not country_code:
            raise exceptions.ValidationError(_("Incorrect country code."))
        return country_code.upper()

    def tbai_get_partner_vat_number(self):
        country_code, vat_number = \
            self.vat and tbai_utils.split_vat(self.vat) or (None, None)
        if not ustr(country_code).encode('utf-8').isalpha():
            vat_number = self.vat
        return vat_number

    def tbai_get_value_apellidos_nombre_razon_social(self):
        """ V 1.2
        <element name="ApellidosNombreRazonSocial" type="T:TextMax120Type"/>
            <maxLength value="120"/>
        :return: Name and surname, or business name
        """
        name = self.commercial_partner_id.name
        return name.strip()[:120]  # Remove leading and trailing whitespace

    def tbai_get_value_nif(self):
        """ V 1.2
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
            tbai_utils.check_spanish_vat_number(_(
                '%s VAT Number') % self.name, vat_number)
            res = vat_number
        else:
            res = ''
        return res

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
        return ', '.join([x for x in address_fields if x])
