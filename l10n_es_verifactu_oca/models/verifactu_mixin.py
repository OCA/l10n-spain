# Copyright 2024 Aures TIC - Jose Zambudio
# Copyright 2024 Aures TIC - Almudena de La Puente
# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import io
import json
from hashlib import sha256
from urllib.parse import urlencode

import psycopg2
import qrcode

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare

from odoo.addons.l10n_es_aeat.models.aeat_mixin import round_by_keys

VERIFACTU_VERSION = 1.0
VERIFACTU_DATE_FORMAT = "%d-%m-%Y"
VERIFACTU_MACRODATA_LIMIT = 100000000.0

VERIFACTU_STATES = [
    ("incorrect", "Incorrect"),
]


class VerifactuMixin(models.AbstractModel):
    _name = "verifactu.mixin"
    _inherit = "aeat.mixin"
    _description = "VERI*FACTU mixin"

    verifactu_enabled = fields.Boolean(
        string="VERI*FACTU enabled",
        compute="_compute_verifactu_enabled",
        search="_search_verifactu_enabled",
    )
    verifactu_hash_string = fields.Char(
        string="VERI*FACTU hash string", copy=False, tracking=True
    )
    verifactu_hash = fields.Char(string="VERI*FACTU hash", copy=False, tracking=True)
    verifactu_refund_type = fields.Selection(
        string="VERI*FACTU refund type",
        selection=[
            # ('S', 'By substitution'), - TODO: no está soportado por el momento
            ("I", "By differences"),
        ],
        compute="_compute_verifactu_refund_type",
        store=True,
        readonly=False,
    )
    verifactu_description = fields.Text(string="VERI*FACTU description", copy=False)
    verifactu_macrodata = fields.Boolean(
        string="VERI*FACTU macrodata?",
        help="Check to confirm that the document has an absolute amount "
        "greater o equal to 100 000 000,00 euros.",
        compute="_compute_verifactu_macrodata",
    )
    verifactu_csv = fields.Char(string="VERI*FACTU CSV", copy=False, readonly=True)
    verifactu_return = fields.Text(
        string="VERI*FACTU return", copy=False, readonly=True
    )
    verifactu_registration_date = fields.Datetime(
        string="VERI*FACTU registration date", copy=False
    )
    verifactu_registration_key = fields.Many2one(
        string="VERI*FACTU registration key",
        comodel_name="verifactu.registration.key",
        compute="_compute_verifactu_registration_key",
        store=True,
        readonly=False,
    )
    verifactu_tax_key = fields.Selection(
        string="VERI*FACTU tax key",
        selection="_get_verifactu_tax_keys",
        compute="_compute_verifactu_tax_key",
        store=True,
        readonly=False,
    )
    verifactu_registration_key_code = fields.Char(
        string="VERI*FACTU key code", compute="_compute_verifactu_registration_key_code"
    )
    verifactu_qr_url = fields.Char(
        string="VERI*FACTU URL", compute="_compute_verifactu_qr_url"
    )
    verifactu_qr = fields.Binary(
        string="VERI*FACTU QR", compute="_compute_verifactu_qr"
    )
    verifactu_send_date = fields.Datetime(
        string="VERI*FACTU send date", index=True, copy=False
    )
    verifactu_invoice_entry_ids = fields.One2many(
        comodel_name="verifactu.invoice.entry",
        inverse_name="document_id",
        domain=lambda doc: [("model", "=", doc._name)],
        string="VERI*FACTU invoice entries",
        readonly=True,
        copy=False,
    )
    verifactu_response_line_ids = fields.One2many(
        comodel_name="verifactu.invoice.entry.response.line",
        inverse_name="document_id",
        domain=lambda doc: [("model", "=", doc._name)],
        string="VERI*FACTU response lines",
        readonly=True,
        copy=False,
    )
    last_verifactu_invoice_entry_id = fields.Many2one(
        comodel_name="verifactu.invoice.entry",
        string="VERI*FACTU last invoice entry",
        readonly=True,
        copy=False,
    )
    last_verifactu_response_line_id = fields.Many2one(
        comodel_name="verifactu.invoice.entry.response.line",
        string="VERI*FACTU response line",
        readonly=True,
        copy=False,
    )
    aeat_state = fields.Selection(
        selection_add=VERIFACTU_STATES,
        compute="_compute_aeat_state",
        store=True,
        copy=False,
    )

    @api.depends("last_verifactu_response_line_id.send_state")
    def _compute_aeat_state(self):
        for document in self:
            if document.verifactu_enabled and document.last_verifactu_response_line_id:
                document.aeat_state = (
                    document.last_verifactu_response_line_id.send_state
                )

    @api.model
    def _get_verifactu_reference_models(self):
        """This method is used to define the models that can be used as
        previous documents in the VERI*FACTU mixin.
        """
        return ["account.move"]

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
        """  # noqa: E501
        for record in self:
            # FIXME: Not be hard-coded
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
            qr_url = urlencode(qr_values, encoding="utf-8")
            record.verifactu_qr_url = f"{qr_base_url}?{qr_url}"

    def _compute_verifactu_qr(self):
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

    def _compute_verifactu_registration_key(self):
        raise NotImplementedError()

    def _compute_verifactu_tax_key(self):
        raise NotImplementedError()

    @api.depends("verifactu_registration_key")
    def _compute_verifactu_registration_key_code(self):
        for record in self:
            record.verifactu_registration_key_code = (
                record.verifactu_registration_key.code
            )

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
        """Datos del desarrollador del sistema informático."""
        if not self.company_id.verifactu_developer_id:
            raise UserError(
                _("Please, configure the VERI*FACTU developer in your company")
            )
        developer = self.company_id.verifactu_developer_id
        chaining = self._get_verifactu_chaining()
        verifactu_companies = (
            self.env["res.company"]
            .sudo()
            .search_count([("verifactu_enabled", "=", True)])
        )
        return {
            "NombreRazon": developer.name,
            "NIF": developer.vat,
            "NombreSistemaInformatico": developer.sif_name,
            "IdSistemaInformatico": chaining.sif_id,
            "Version": developer.version,
            "NumeroInstalacion": chaining.installation_number,
            "TipoUsoPosibleSoloVerifactu": "S",
            "TipoUsoPosibleMultiOT": "S",
            "IndicadorMultiplesOT": "S" if verifactu_companies > 1 else "N",
            "IDOtro": {
                "IDType": "",
                "ID": "",
            },
        }

    def _get_verifactu_chaining_invoice_dict(self):
        raise NotImplementedError

    def _aeat_check_exceptions(self):
        """Inheritable method for exception control when sending VERI*FACTU invoices."""
        res = super()._aeat_check_exceptions()
        if self.company_id.verifactu_enabled and not self.verifactu_enabled:
            raise UserError(_("This invoice is not VERI*FACTU enabled."))
        return res

    def _get_verifactu_date(self, date):
        datetimeobject = fields.Date.to_date(date)
        return datetimeobject.strftime(VERIFACTU_DATE_FORMAT)

    def _get_verifactu_hash_string(self):
        raise NotImplementedError

    def _get_verifactu_chaining(self):
        return NotImplementedError

    def _generate_verifactu_chaining(self, entry_type=False):
        """Generate VERI*FACTU invoice entry for company-wide chaining."""
        self.ensure_one()
        chaining = self._get_verifactu_chaining()
        chaining.flush_recordset(["last_verifactu_invoice_entry_id"])
        try:
            with self.env.cr.savepoint():
                self.env.cr.execute(
                    f"SELECT last_verifactu_invoice_entry_id FROM {chaining._table}"
                    " WHERE id = %s FOR UPDATE NOWAIT",
                    [chaining.id],
                )
                result = self.env.cr.fetchone()
                previous_invoice_entry_id = result[0] if result and result[0] else False
                invoice_vals = {
                    "verifactu_chaining_id": chaining.id,
                    "model": self._name,
                    "document_id": self.id,
                    "document_name": self.name,
                    "previous_invoice_entry_id": previous_invoice_entry_id,
                    "company_id": self.company_id.id,
                    "document_hash": "",
                }
                if entry_type:
                    invoice_vals["entry_type"] = entry_type
                invoice_entry = self.env["verifactu.invoice.entry"].create(invoice_vals)
                self.last_verifactu_invoice_entry_id = invoice_entry
                verifactu_hash_values = self._get_verifactu_hash_string()
                self.verifactu_hash_string = verifactu_hash_values
                hash_string = sha256(verifactu_hash_values.encode("utf-8"))
                self.verifactu_hash = hash_string.hexdigest().upper()
                # Generate JSON data for AEAT
                aeat_json_data = ""
                try:
                    inv_dict = self._get_verifactu_invoice_dict()
                    aeat_json_data = json.dumps(inv_dict, indent=4)
                except Exception:
                    # If JSON generation fails, store empty string
                    aeat_json_data = ""
                invoice_entry.document_hash = hash_string.hexdigest().upper()
                invoice_entry.aeat_json_data = aeat_json_data
                self.env.cr.execute(
                    f"UPDATE {chaining._table} "
                    "SET last_verifactu_invoice_entry_id = %s WHERE id = %s",
                    [invoice_entry.id, chaining.id],
                )
                chaining.invalidate_recordset(["last_verifactu_invoice_entry_id"])
        except psycopg2.OperationalError as err:
            if err.pgcode == "55P03":  # could not obtain the lock
                raise UserError(
                    _(
                        "Could not obtain last document sent to VERI*FACTU for "
                        "chaining %s.",
                        chaining.name,
                    )
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

    def _get_verifactu_accepted_tax_agencies(self):
        return ["l10n_es_aeat.aeat_tax_agency_spain"]

    def _check_verifactu_configuration(self, suffixes=None):
        prefix = _("The invoice %s cannot be sent to VERI*FACTU because:")
        if not suffixes:
            suffixes = []
        if not self._get_verifactu_chaining():
            suffixes.append(
                _("- Your company does not have a VERI*FACTU chaining configured.")
            )
        if not self.company_id.tax_agency_id:
            suffixes.append(_("- Your company does not have a tax agency configured."))
        if (
            self.company_id.tax_agency_id.get_external_id
            in self._get_verifactu_accepted_tax_agencies()
        ):
            suffixes.append(_("- Your company's tax agency is not supported."))
        if not self.company_id.verifactu_developer_id:
            suffixes.append(
                _("- Your company does not have a VERI*FACTU developer configured.")
            )
        if not self.company_id.country_code or self.company_id.country_code != "ES":
            suffixes.append(_("Your company is not registered in Spain."))
        if suffixes:
            raise UserError((prefix + "\n".join(suffixes)) % self[self._rec_name])

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
        ).tax_xmlid_ids
        mapped_taxes = self.env["account.tax"]
        for template in tax_templates:
            tax_id = self.company_id._get_tax_id_from_xmlid(template.name)
            mapped_taxes |= self.env["account.tax"].browse(tax_id)
        return mapped_taxes

    def _raise_exception_verifactu(self, field_name):
        raise UserError(
            _(
                "You cannot change the %s of document "
                "already registered at VERI*FACTU. You must cancel the "
                "document and create a new one with the correct value."
            )
            % field_name
        )

    @api.model
    def _get_verifactu_batch(self):
        try:
            return int(
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("l10n_es_verifactu_oca.verifactu_batch", "1000")
            )
        except ValueError as e:
            raise UserError(
                _(
                    "The value in l10n_es_verifactu_oca.verifactu_batch "
                    "system parameter must be an integer. Please, check the "
                    "value of the parameter."
                )
            ) from e
