# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, exceptions, fields, models
from odoo.tools.misc import ustr

from ..utils import utils as tbai_utils
from .ticketbai_invoice_customer import TicketBaiCustomerIdType


class ResPartner(models.Model):
    _inherit = "res.partner"

    tbai_enabled = fields.Boolean(compute="_compute_tbai_enabled")
    tbai_partner_idtype = fields.Selection(
        selection=[
            (TicketBaiCustomerIdType.T02.value, "VAT identification number"),
            (TicketBaiCustomerIdType.T03.value, "Passport"),
            (
                TicketBaiCustomerIdType.T04.value,
                "Official identification document issued by "
                "the country or territory of residence",
            ),
            (TicketBaiCustomerIdType.T05.value, "Residence certificate"),
            (TicketBaiCustomerIdType.T06.value, "Other document"),
        ],
        string="TicketBAI Identification Type Code",
        default=TicketBaiCustomerIdType.T02.value,
    )
    tbai_partner_identification_number = fields.Char(
        "TicketBAI Partner Identification Number",
        default="",
        help="Used when the identification type code is not VAT identification number.",
    )

    @api.constrains("tbai_partner_identification_number")
    def _check_tbai_partner_identification_number(self):
        for record in self:
            if record.tbai_partner_identification_number:
                if 20 < len(record.tbai_partner_identification_number):
                    raise exceptions.ValidationError(
                        _(
                            "Partner Identification Number %s longer than expected. "
                            "Should be 20 characters max.!"
                        )
                        % record.name
                    )

    def tbai_get_partner_country_code(self):
        country_code, vat_number = (
            self.vat and tbai_utils.split_vat(self.vat) or (None, None)
        )
        if not ustr(country_code).encode("utf-8").isalpha():
            country_code = self.commercial_partner_id.country_id.code
        elif isinstance(country_code, str):
            country_code = country_code
        elif self.country_id:
            country_code = self.country_id.code
        if not country_code:
            raise exceptions.ValidationError(
                _("The invoice customer %s does not have a valid country assigned.")
                % self.name
            )
        return country_code.upper()

    def tbai_get_partner_vat_number(self):
        country_code, vat_number = (
            self.vat and tbai_utils.split_vat(self.vat) or (None, None)
        )
        if not ustr(country_code).encode("utf-8").isalpha():
            vat_number = self.vat
        return vat_number

    def tbai_get_value_apellidos_nombre_razon_social(self):
        """V 1.2
        <element name="ApellidosNombreRazonSocial" type="T:TextMax120Type"/>
            <maxLength value="120"/>
        :return: Name and surname, or business name
        """
        name = self.commercial_partner_id.name
        return name.strip()[:120]  # Remove leading and trailing whitespace

    def tbai_get_value_nif(self):
        """V 1.2
        <element name="NIF" type="T:NIFType"/>
            <length value="9" />
            <pattern value="(([a-z|A-Z]{1}\\d{7}[a-z|A-Z]{1})|(\\d{8}[a-z|A-Z]{1})|
            ([a-z|A-Z]{1}\\d{8}))" />
        :return: VAT Number for Customers from Spain or the Company associated partner.
        """
        country_code = self.tbai_get_partner_country_code()
        vat_number = self.tbai_get_partner_vat_number()
        if (
            vat_number
            and country_code
            and self.env.ref("base.es").code.upper() == country_code
        ):
            tbai_utils.check_spanish_vat_number(
                _("%s VAT Number") % self.name, vat_number
            )
            res = vat_number
        else:
            res = ""
        return res

    def tbai_get_value_direccion(self):
        """V 1.2
        <element name="Direccion" type="T:TextMax250Type" minOccurs="0"/>
            <maxLength value="250"/>
        """
        address_fields = [
            "%s" % (self.street or ""),
            "%s" % (self.street2 or ""),
            ("{} {}".format(self.zip or "", self.city or "")).strip(),
            "%s" % (self.state_id.name or ""),
            "%s" % (self.country_id.name or ""),
        ]
        return ", ".join([x for x in address_fields if x])

    @api.depends("company_id")
    def _compute_tbai_enabled(self):
        tbai_enabled = any(self.env.companies.mapped("tbai_enabled"))
        for partner in self:
            partner.tbai_enabled = (
                partner.company_id.tbai_enabled if partner.company_id else tbai_enabled
            )
