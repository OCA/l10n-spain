# Copyright 2024 Aures TIC - Jose Zambudio <jose@aurestic.es>
# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import io
import json
import logging
from hashlib import sha256
from urllib.parse import urlencode

import psycopg2

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare

from odoo.addons.l10n_es_aeat.models.aeat_mixin import round_by_keys

_logger = logging.getLogger(__name__)

try:
    import qrcode
except (ImportError, IOError) as err:
    qrcode = None
    _logger.error(err)

###########################################
# revisar los imports que no hagan falta
# cuando funcione bien el _connect_aeat sin tener que poner
# el forbid_entities, y se pueda borrar la función _connect_verifactu
# de este fichero para usar la del aeat_mixin


_logger = logging.getLogger(__name__)

VERIFACTU_VERSION = 1.0
VERIFACTU_DATE_FORMAT = "%d-%m-%Y"
VERIFACTU_MACRODATA_LIMIT = 100000000.0


class VerifactuMixin(models.AbstractModel):
    _name = "verifactu.mixin"
    _inherit = "aeat.mixin"
    _description = "Verifactu Mixin"

    verifactu_enabled = fields.Boolean(
        string="Enable AEAT",
        compute="_compute_verifactu_enabled",
        search="_search_verifactu_enabled",
    )
    verifactu_hash_string = fields.Char(copy=False, tracking=True)
    verifactu_hash = fields.Char(copy=False, tracking=True)
    verifactu_refund_type = fields.Selection(
        selection=[
            # ('S', 'By substitution'), - en sii no está soportado, aquí igual?
            ("I", "By differences"),
        ],
        compute="_compute_verifactu_refund_type",
        store=True,
        readonly=False,
    )
    verifactu_description = fields.Text(
        copy=False,
    )
    verifactu_macrodata = fields.Boolean(
        string="MacroData",
        help="Check to confirm that the document has an absolute amount "
        "greater o equal to 100 000 000,00 euros.",
        compute="_compute_verifactu_macrodata",
    )
    verifactu_csv = fields.Char(copy=False, readonly=True)
    verifactu_return = fields.Text(copy=False, readonly=True)
    verifactu_registration_date = fields.Datetime(copy=False)
    verifactu_registration_key = fields.Many2one(
        comodel_name="verifactu.registration.keys",
    )
    verifactu_tax_key = fields.Selection(
        string="Verifactu tax key",
        selection="_get_verifactu_tax_keys",
    )
    verifactu_registration_key_code = fields.Char(
        string="Verifactu Code",
    )
    verifactu_qr_url = fields.Char("URL", compute="_compute_verifactu_qr_url")
    verifactu_qr = fields.Binary(string="QR", compute="_compute_verifactu_qr")
    verifactu_invoice_entry_id = fields.Many2one(
        "verifactu.invoice",
        string="VeriFactu Invoice Entry",
        readonly=True,
        copy=False,
    )
    verifactu_previous_document_id = fields.Reference(
        string="Previous Verifactu Document",
        selection="_selection_verifactu_reference_models",
        readonly=True,
        copy=False,
        compute="_compute_verifactu_previous_document_id",
        store=True,
    )
    verifactu_next_document_id = fields.Reference(
        string="Next Verifactu Document",
        selection="_selection_verifactu_reference_models",
        readonly=True,
        copy=False,
    )
    verifactu_send_date = fields.Datetime(index=True, copy=False)

    @api.model
    def _selection_verifactu_reference_models(self):
        # this method is used to define the models that can be used as
        # previous documents in the verifactu mixin
        return [("account.move", "Invoice")]

    def _compute_verifactu_enabled(self):
        raise NotImplementedError

    def _compute_verifactu_macrodata(self):
        for document in self:
            document.verifactu_macrodata = (
                float_compare(
                    abs(document._get_verifactu_amount_total()),
                    VERIFACTU_MACRODATA_LIMIT,
                    precision_digits=2,
                )
                >= 0
            )

    def _compute_verifactu_qr_url(self):
        """Returns the URL to be used in the QR code. A sample URL would be (urlencoded):
        https://prewww2.aeat.es/wlpl/TIKECONT/ValidarQR?nif=89890001K&numserie=12345678%26G33&fecha=01-01-2024&importe=241.4
        """  # noqa: B950
        for record in self:
            agency = self.env.ref("l10n_es_aeat.aeat_tax_agency_spain")
            if record.company_id.verifactu_test:
                qr_base_url = agency.verifactu_qr_base_url_test_address
            else:
                qr_base_url = agency.verifactu_qr_base_url

            qr_values = record._get_verifactu_qr_values()

            # Check all values are ASCII between 32 and 126
            for value in qr_values.values():
                try:
                    str(value).encode("ascii")
                except UnicodeEncodeError as uee:
                    raise UserError(
                        _("QR URL value '{}' is not ASCII").format(value)
                    ) from uee

            # Build QR URL
            qr_url = "{}?{}".format(
                qr_base_url,
                urlencode(qr_values, encoding="utf-8"),
            )

            record.verifactu_qr_url = qr_url

    def _compute_verifactu_qr(self):
        # If qrcode module is not available, we can't generate QR codes
        if not qrcode:
            _logger.error("qrcode module is not available")
            return
        for record in self:
            if record.state != "posted" or not record.verifactu_enabled:
                record.verifactu_qr = False
                continue
            qr = qrcode.QRCode(
                border=0, error_correction=qrcode.constants.ERROR_CORRECT_M
            )
            qr.add_data(record.verifactu_qr_url)
            qr.make()
            img = qr.make_image()
            with io.BytesIO() as temp:
                img.save(temp, format="PNG")
                record.verifactu_qr = base64.b64encode(temp.getvalue())

    @api.model
    def _search_verifactu_enabled(self, operator, value):
        if operator not in ("=", "!="):
            raise ValueError(_("Unsupported search operator"))
        return [("company_id.verifactu_enabled", operator, value)]

    def _get_verifactu_qr_values(self):
        raise NotImplementedError

    @api.model
    def _get_verifactu_tax_keys(self):
        return self.env["account.fiscal.position"]._get_verifactu_tax_keys()

    def _connect_verifactu_params_aeat(self, mapping_key):
        self.ensure_one()
        agency = self.company_id.tax_agency_id
        if not agency:
            # We use spanish agency by default to keep old behavior with
            # ir.config parameters. In the future it might be good to reinforce
            # to explicitly set a tax agency in the company by raising an error
            # here.
            agency = self.env.ref("l10n_es_aeat.aeat_tax_agency_spain")
        return agency._connect_params_verifactu(self.company_id)

    def _get_verifactu_invoice_dict(self):
        self.ensure_one()
        inv_dict = {}
        mapping_key = self._get_mapping_key()
        if mapping_key in ["out_invoice", "out_refund"]:
            inv_dict = self._get_verifactu_invoice_dict_out()
        else:
            raise NotImplementedError
        round_by_keys(
            inv_dict,
            [
                "BaseImponibleOimporteNoSujeto",
                "CuotaRepercutida",
                "TipoRecargoEquivalencia",
                "CuotaRecargoEquivalencia",
                "CuotaTotal",
                "ImporteTotal",
                "BaseRectificada",
                "CuotaRectificada",
            ],
        )
        return inv_dict

    def _get_verifactu_developer_dict(self):
        """
        Datos del desarrollador del sistema informático
        """
        if not self.company_id.verifactu_developer_id:
            raise UserError(
                _("Please, configure the verifactu developer in your company")
            )
        developer = self.company_id.verifactu_developer_id
        spanish_companies = (
            self.env["res.company"]
            .sudo()
            .search_count(
                [("partner_id.country_id", "=", self.env.ref("base.es").id)], limit=2
            )
        )
        return {
            "NombreRazon": developer.name,
            "NIF": developer.vat,
            "NombreSistemaInformatico": developer.sif_name,
            "IdSistemaInformatico": developer.sif_id,
            "Version": developer.version,
            "NumeroInstalacion": developer.installation_number,
            "TipoUsoPosibleSoloVerifactu": "S",
            "TipoUsoPosibleMultiOT": "S",
            "IndicadorMultiplesOT": "S" if spanish_companies > 1 else "N",
            "IDOtro": {
                "IDType": "",
                "ID": "",
            },
        }

    @api.depends("verifactu_invoice_entry_id")
    def _compute_verifactu_previous_document_id(self):
        """Compute the previous document based on the invoice entry."""
        for record in self:
            if (
                record.verifactu_invoice_entry_id
                and record.verifactu_invoice_entry_id.previous_invoice_entry_id
            ):
                record.verifactu_previous_document_id = (
                    record.verifactu_invoice_entry_id.previous_invoice_entry_id.document_id
                )
            else:
                record.verifactu_previous_document_id = False

    def _get_verifactu_chaining_invoice_dict(self):
        raise NotImplementedError

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

    def _get_verifactu_hash_string(self):
        raise NotImplementedError

    def _generate_verifactu_chaining(self):
        """Generate verifactu invoice entry for company-wide chaining."""
        self.ensure_one()

        # Always use company for invoice chaining
        company = self.company_id

        company.flush_recordset(["last_verifactu_invoice_entry_id"])

        try:
            with self.env.cr.savepoint():
                self.env.cr.execute(
                    f"SELECT last_verifactu_invoice_entry_id FROM {company._table}"
                    " WHERE id = %s FOR UPDATE NOWAIT",
                    [company.id],
                )
                result = self.env.cr.fetchone()
                previous_invoice_entry_id = result[0] if result and result[0] else False

                prev_doc = False
                if previous_invoice_entry_id:
                    previous_invoice_entry = self.env["verifactu.invoice"].browse(
                        previous_invoice_entry_id
                    )
                    if previous_invoice_entry.document_id:
                        prev_doc = previous_invoice_entry.document_id

                self.verifactu_previous_document_id = prev_doc

                verifactu_hash_values = self._get_verifactu_hash_string()
                self.verifactu_hash_string = verifactu_hash_values
                hash_string = sha256(verifactu_hash_values.encode("utf-8"))
                self.verifactu_hash = hash_string.hexdigest().upper()

                if prev_doc:
                    prev_doc.verifactu_next_document_id = self

                # Generate JSON data for AEAT
                aeat_json_data = ""
                try:
                    inv_dict = self._get_verifactu_invoice_dict()
                    aeat_json_data = json.dumps(inv_dict, indent=4)
                except Exception:
                    # If JSON generation fails, store empty string
                    aeat_json_data = ""

                invoice_vals = {
                    "document_id": f"{self._name},{self.id}",
                    "previous_invoice_entry_id": previous_invoice_entry_id,
                    "company_id": self.company_id.id,
                    "document_hash": self.verifactu_hash,
                    "aeat_json_data": aeat_json_data,
                }

                invoice_entry = self.env["verifactu.invoice"].create(invoice_vals)
                self.verifactu_invoice_entry_id = invoice_entry

                self.env.cr.execute(
                    f"UPDATE {company._table} "
                    "SET last_verifactu_invoice_entry_id = %s WHERE id = %s",
                    [invoice_entry.id, company.id],
                )

                company.invalidate_recordset(["last_verifactu_invoice_entry_id"])

        except psycopg2.OperationalError as err:
            if err.pgcode == "55P03":  # could not obtain the lock
                raise UserError(
                    _(
                        "Could not obtain last document sent to verifactu for company %s."
                    )
                    % company.name
                ) from err
            raise

    def _get_verifactu_document_type(self):
        raise NotImplementedError()

    def _get_verifactu_description(self):
        raise NotImplementedError()

    def _get_verifactu_taxes_and_total(self):
        raise NotImplementedError

    def _get_verifactu_version(self):
        return VERIFACTU_VERSION

    def _get_verifactu_receiver_dict(self):
        raise NotImplementedError

    def _compute_verifactu_refund_type(self):
        self.verifactu_refund_type = False

    def _is_aeat_simplified_invoice(self):
        """Inheritable method to allow control when an
        invoice are simplified or normal"""
        partner = self._aeat_get_partner()
        return partner.aeat_simplified_invoice

    def _check_verifactu_configuration(self):
        if not self.company_id.tax_agency_id:
            raise UserError(
                _(
                    "The document %s cannot be sent to Verifactu because your "
                    "company does not have a tax agency configured."
                )
                % self.name
            )
        if self.company_id.tax_agency_id != self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_spain"
        ):
            raise UserError(
                _(
                    "The document %s cannot be sent to Verifactu because your "
                    "company's tax agency is not the Spanish Tax Agency(AEAT)."
                )
                % self.name
            )
        if not self.company_id.verifactu_developer_id:
            raise UserError(
                _(
                    "The document %s cannot be sent to Verifactu because your "
                    "company does not have a verifactu developer configured."
                )
                % self.name
            )
        if not self.company_id.country_code or self.company_id.country_code != "ES":
            raise UserError(
                _(
                    "The document %s cannot be sent to Verifactu because your "
                    "company is not registered in Spain."
                )
                % self.name
            )
        return

    @api.model
    def _get_verifactu_map(self, date):
        return (
            self.env["verifactu.map"]
            .sudo()
            .with_context(active_test=False)
            .search(
                [
                    "|",
                    ("date_from", "<=", date),
                    ("date_from", "=", False),
                    "|",
                    ("date_to", ">=", date),
                    ("date_to", "=", False),
                ],
                limit=1,
            )
        )

    @api.model
    def _get_verifactu_taxes_map(self, codes, date):
        """Return the codes that correspond to verifactu map line codes.

        :param codes: List of code strings to get the mapping.
        :param date: Date to map
        :return: Recordset with the corresponding codes
        """
        verifactu_map = self._get_verifactu_map(date)
        tax_templates = verifactu_map.map_lines.filtered(
            lambda x: x.code in codes
        ).taxes
        return self.company_id.get_taxes_from_templates(tax_templates)

    def _raise_exception_verifactu(self, field_name):
        raise UserError(
            _(
                "You cannot change the %s of document"
                "already registered at Verifactu. You must cancel the "
                "document and create a new one with the correct value"
            )
            % field_name
        )

    @api.model
    def _get_verifactu_batch(self):
        try:
            return int(
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("l10n_es_verifactu.verifactu_batch", "50")
            )
        except ValueError as e:
            raise UserError(
                _(
                    "The value in l10n_es_verifactu.verifactu_batch "
                    "system parameter must be an integer. Please, check the "
                    "value of the parameter."
                )
            ) from e
