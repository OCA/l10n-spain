# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from collections import OrderedDict

from odoo import _, api, exceptions, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    tbai_enabled = fields.Boolean("Enable TicketBAI", copy=False)
    tbai_test_available = fields.Boolean("Are Tests URLs Available", copy=False)
    tbai_pro_available = fields.Boolean("Are Production URLs Available", copy=False)
    tbai_test_enabled = fields.Boolean("Enable testing", copy=False)
    tbai_certificate_id = fields.Many2one(
        comodel_name="tbai.certificate",
        string="Certificate",
        domain="[('company_id', '=', id)]",
        copy=False,
    )
    tbai_installation_id = fields.Many2one(comodel_name="tbai.installation", copy=False)
    tbai_license_key = fields.Char(
        "License Key", related="tbai_installation_id.license_key", readonly=True
    )
    tbai_developer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Developer",
        related="tbai_installation_id.developer_id",
        readonly=True,
    )
    tbai_software_name = fields.Char(
        string="Software Name",
        related="tbai_installation_id.name",
        readonly=True,
        help="Registered name at the Tax Agency.",
    )
    tbai_software_version = fields.Char(
        string="Software Version",
        related="tbai_installation_id.version",
        copy=False,
        help="Version of the software.",
    )
    tbai_device_serial_number = fields.Char(
        "Device Serial Number", default="", copy=False
    )
    tbai_tax_agency_id = fields.Many2one(
        comodel_name="tbai.tax.agency", string="TBAI Tax Agency", copy=False
    )
    tbai_vat_regime_simplified = fields.Boolean("Regime Simplified", copy=False)
    tbai_last_invoice_id = fields.Many2one(
        string="Last TicketBAI Invoice sent", comodel_name="tbai.invoice", copy=False
    )

    @api.constrains("tbai_certificate_id")
    def _check_tbai_certificate_id(self):
        for record in self:
            if record.tbai_enabled and not record.tbai_certificate_id:
                raise exceptions.ValidationError(
                    _("Company %s TicketBAI Certificate is required.") % record.name
                )

    @api.constrains("tbai_device_serial_number")
    def _check_tbai_device_serial_number(self):
        for record in self:
            if (
                record.tbai_enabled
                and record.tbai_device_serial_number
                and 30 < len(record.tbai_device_serial_number)
            ):
                raise exceptions.ValidationError(
                    _(
                        "Company %s Device Serial Number longer than expected. "
                        "Should be 30 characters max.!"
                    )
                    % record.name
                )

    @api.onchange("tbai_tax_agency_id")
    def onchange_tbai_tax_agency(self):
        if not (
            self.tbai_tax_agency_id.test_qr_base_url
            and self.tbai_tax_agency_id.test_rest_url_invoice
            and self.tbai_tax_agency_id.test_rest_url_cancellation
        ):
            self.tbai_test_available = False
            self.tbai_test_enabled = False
        else:
            self.tbai_test_available = True
        if not (
            self.tbai_tax_agency_id.qr_base_url
            and self.tbai_tax_agency_id.rest_url_invoice
            and self.tbai_tax_agency_id.rest_url_cancellation
        ):
            self.tbai_pro_available = False
            self.tbai_test_enabled = True
        else:
            self.tbai_pro_available = True

    @api.onchange("tbai_enabled")
    def onchange_tbai_enabled(self):
        if not self.tbai_enabled:
            self.tbai_test_enabled = False
            self.tbai_license_key = ""
            self.tbai_developer_id = False
            self.tbai_software_name = ""
            self.tbai_device_serial_number = ""
            self.tbai_tax_agency_id = False
            self.tbai_vat_regime_simplified = False
            self.tbai_certificate_id = False

    @api.constrains("tbai_tax_agency_id")
    def _check_tbai_tax_agency_id(self):
        for record in self:
            if record.tbai_enabled and not record.tbai_tax_agency_id:
                raise exceptions.ValidationError(
                    _("Company %s TicketBAI Tax Agency is required.") % record.name
                )

            tbai_invoices = record.env["tbai.invoice"].search(
                [("company_id", "=", record.id)]
            )

            if 0 < len(tbai_invoices):
                raise exceptions.ValidationError(
                    _(
                        "Tax agency cannot be modified after a TicketBAI "
                        "invoice has been sent."
                    )
                )

    def tbai_certificate_get_p12_buffer(self):
        if self.tbai_certificate_id:
            return self.tbai_certificate_id.get_p12_buffer()
        else:
            return None

    def tbai_certificate_get_p12(self):
        if self.tbai_certificate_id:
            return self.tbai_certificate_id.get_p12()
        else:
            return None

    def tbai_certificate_get_p12_password(self):
        if self.tbai_certificate_id:
            return self.tbai_certificate_id.password
        else:
            return None

    def _tbai_build_entidad_desarrolladora(self):
        res = OrderedDict()
        nif = self.tbai_developer_id.tbai_get_value_nif()
        if nif:
            res["NIF"] = nif
        else:
            id_otro = self.tbai_developer_id.tbai_build_id_otro()
            if id_otro:
                res["IDOtro"] = id_otro
        if "NIF" not in res and "IDOtro" not in res:
            raise exceptions.ValidationError(
                _(
                    "TicketBAI Developer %s VAT Number or another "
                    "type of identification is required."
                )
                % self.tbai_developer_id.name
            )
        return res

    def tbai_build_software(self):
        return OrderedDict(
            [
                ("LicenciaTBAI", self.tbai_license_key),
                ("EntidadDesarrolladora", self._tbai_build_entidad_desarrolladora()),
                ("Nombre", self.tbai_software_name),
                ("Version", self.tbai_software_version),
            ]
        )
