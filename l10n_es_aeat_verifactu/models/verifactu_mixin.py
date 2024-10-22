# Copyright 2024 Aures TIC - Jose Zambudio <jose@aurestic.es>
# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from hashlib import sha256

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_es_aeat.models.aeat_mixin import round_by_keys

VERIFACTU_VERSION = "0.12.2"
VERIFACTU_DATE_FORMAT = "%d-%m-%Y"


class VerifactuMixin(models.AbstractModel):
    _name = "verifactu.mixin"
    _inherit = "aeat.mixin"
    _description = "Verifactu Mixin"

    verifactu_enabled = fields.Boolean(
        string="Enable AEAT",
        compute="_compute_verifactu_enabled",
    )
    verifactu_hash_string = fields.Char(compute="_compute_verifactu_hash")
    verifactu_hash = fields.Char(compute="_compute_verifactu_hash")

    def _compute_verifactu_enabled(self):
        raise NotImplementedError

    def _connect_params_aeat(self, mapping_key):
        self.ensure_one()
        agency = self.company_id.tax_agency_id
        if not agency:
            # We use spanish agency by default to keep old behavior with
            # ir.config parameters. In the future it might be good to reinforce
            # to explicitly set a tax agency in the company by raising an error
            # here.
            agency = self.env.ref("l10n_es_aeat.aeat_tax_agency_spain")
        return agency._connect_params_verifactu(mapping_key, self.company_id)

    def _get_aeat_header(self, tipo_comunicacion=False, cancellation=False):
        """Builds VERIFACTU send header

        :param tipo_comunicacion String 'A0': new reg, 'A1': modification
        :param cancellation Bool True when the communitacion es for document
            cancellation
        :return Dict with header data depending on cancellation
        """
        self.ensure_one()
        if not self.company_id.vat:
            raise UserError(
                _("No VAT configured for the company '{}'").format(self.company_id.name)
            )
        header = {
            "IDVersion": VERIFACTU_VERSION,
            "ObligadoEmision": {
                "NombreRazon": self.company_id.name[0:120],
                "NIF": self.company_id.partner_id._parse_aeat_vat_info()[2],
            },
            # "TipoRegistroAEAT": ,
            # "FechaFinVeriactu": ,
        }
        # if not cancellation:
        #     header.update({"TipoComunicacion": tipo_comunicacion})
        return header

    def _get_aeat_invoice_dict(self):
        self.ensure_one()
        inv_dict = {}
        mapping_key = self._get_mapping_key()
        if mapping_key in ["out_invoice", "out_refund"]:
            inv_dict = self._get_aeat_invoice_dict_out()
        else:
            raise NotImplementedError
        round_by_keys(
            inv_dict,
            [
                "BaseImponible",
                "CuotaRepercutida",
                "CuotaSoportada",
                "TipoRecargoEquivalencia",
                "CuotaRecargoEquivalencia",
                "ImportePorArticulos7_14_Otros",
                "ImporteTAIReglasLocalizacion",
                "ImporteTotal",
                "BaseRectificada",
                "CuotaRectificada",
                "CuotaDeducible",
                "ImporteCompensacionREAGYP",
            ],
        )
        return inv_dict

    def _get_aeat_invoice_dict_out(self, cancel=False):
        """Build dict with data to send to AEAT WS for document types:
        out_invoice and out_refund.

        :param cancel: It indicates if the dictionary is for sending a
          cancellation of the document.
        :return: documents (dict) : Dict XML with data for this document.
        """
        self.ensure_one()
        document_date = self._change_date_format(self._get_document_date())
        company = self.company_id
        fiscal_year = self._get_document_fiscal_year()
        period = self._get_document_period()
        serial_number = self._get_document_serial_number()
        inv_dict = {
            "IDFactura": {
                "IDEmisorFactura": {
                    "NIF": company.partner_id._parse_aeat_vat_info()[2]
                },
                "NumSerieFactura": serial_number,
                "FechaExpedicionFactura": document_date,
            },
            "PeriodoLiquidacion": {
                "Ejercicio": fiscal_year,
                "Periodo": period,
            },
        }
        return inv_dict

    def _aeat_check_exceptions(self):
        """Inheritable method for exceptions control when sending veri*FACTU invoices."""
        res = super()._aeat_check_exceptions()
        if self.company_id.verifactu_enabled and not self.verifactu_enabled:
            raise UserError(_("This invoice is not veri*FACTU enabled."))
        return res

    def _change_date_format(self, date):
        datetimeobject = fields.Date.to_date(date)
        new_date = datetimeobject.strftime(VERIFACTU_DATE_FORMAT)
        return new_date

    @api.model
    def _get_verifactu_hash_string(self):
        raise NotImplementedError

    def _compute_verifactu_hash(self):
        # TODO  by the moment those fields are not stored,
        # but they must be stored because are unalterable
        # when invoice is sent to verifactu, because the hash depends
        # on previous sent hash..
        for record in self:
            verifactu_hash_values = record._get_verifactu_hash_string()
            record.verifactu_hash_string = verifactu_hash_values
            hash_string = sha256(verifactu_hash_values.encode("utf-8"))
            record.verifactu_hash = hash_string.hexdigest().upper()
