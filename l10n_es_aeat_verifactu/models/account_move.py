# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# Copyright 2024 Aures Tic - Jose Zambudio <jose@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import pytz

from odoo import _, api, fields, models

VERIFACTU_VALID_INVOICE_STATES = ["posted"]


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "verifactu.mixin"]

    verifactu_document_type = fields.Selection(
        selection=lambda self: self._get_verifactu_docuyment_types(),
        default="F1",
    )

    def _get_verifactu_docuyment_types(self):
        return [
            ("F1", _("FACTURA (ART. 6, 7.2 Y 7.3 DEL RD 1619/2012)")),
            (
                "F2",
                _(
                    """FACTURA SIMPLIFICADA Y FACTURAS SIN IDENTIFICACIÓN DEL DESTINATARIO
                    (ART. 6.1.D RD 1619/2012)"""
                ),
            ),
            (
                "R1",
                _("FACTURA RECTIFICATIVA (Art 80.1 y 80.2 y error fundado en derecho)"),
            ),
            ("R2", _("FACTURA RECTIFICATIVA (Art. 80.3)")),
            ("R3", _("FACTURA RECTIFICATIVA (Art. 80.4)")),
            ("R4", _("FACTURA RECTIFICATIVA (Resto)")),
            ("R5", _("FACTURA RECTIFICATIVA EN FACTURAS SIMPLIFICADAS")),
            (
                "F3",
                _(
                    """FACTURA EMITIDA EN SUSTITUCIÓN DE FACTURAS SIMPLIFICADAS FACTURADAS
                    Y DECLARADAS"""
                ),
            ),
        ]

    @api.depends(
        "company_id",
        "company_id.verifactu_enabled",
        "move_type",
        "fiscal_position_id",
        "fiscal_position_id.aeat_active",
    )
    def _compute_verifactu_enabled(self):
        """Compute if the invoice is enabled for the veri*FACTU"""
        for invoice in self:
            if invoice.company_id.verifactu_enabled and invoice.is_invoice():
                invoice.verifactu_enabled = (
                    invoice.fiscal_position_id
                    and invoice.fiscal_position_id.aeat_active
                ) or not invoice.fiscal_position_id
            else:
                invoice.verifactu_enabled = False

    def _get_document_date(self):
        """
        TODO: this method is the same in l10n_es_aeat_sii_oca, so I think that
        it should be directly in l10n_es_aeat
        """
        return self._change_date_format(self.invoice_date)

    def _aeat_get_partner(self):
        """
        TODO: this method is the same in l10n_es_aeat_sii_oca, so I think that
        it should be directly in l10n_es_aeat
        """
        return self.commercial_partner_id

    def _get_document_fiscal_date(self):
        """
        TODO: this method is the same in l10n_es_aeat_sii_oca, so I think that
        it should be directly in l10n_es_aeat
        """
        return self.date

    def _get_mapping_key(self):
        """
        TODO: this method is the same in l10n_es_aeat_sii_oca, so I think that
        it should be directly in l10n_es_aeat
        """
        return self.move_type

    def _get_valid_document_states(self):
        return VERIFACTU_VALID_INVOICE_STATES

    def _get_document_serial_number(self):
        """
        TODO: this method is the same in l10n_es_aeat_sii_oca, so I think that
        it should be directly in l10n_es_aeat
        """
        serial_number = (self.name or "")[0:60]
        if self.thirdparty_invoice:
            serial_number = self.thirdparty_number[0:60]
        return serial_number

    def _get_verifactu_issuer(self):
        return self.company_id.partner_id._parse_aeat_vat_info()[2]

    def _get_verifactu_document_type(self):
        return self.verifactu_document_type or "F1"

    def _get_verifactu_amount_tax(self):
        return self.amount_tax

    def _get_verifactu_amount_total(self):
        return self.amount_total

    def _get_verifactu_previous_hash(self):
        # TODO store it? search it by some kind of sequence?
        return ""

    def _get_verifactu_registration_date(self):
        # Date format must be ISO 8601
        return pytz.utc.localize(self.create_date).isoformat()

    @api.model
    def _get_verifactu_hash_string(self):
        """Gets the verifactu hash string"""
        if (
            not self.verifactu_enabled
            or self.state == "draft"
            or self.move_type not in ("out_invoice", "out_refund")
        ):
            return ""
        issuerID = self._get_verifactu_issuer()
        serialNumber = self._get_document_serial_number()
        expeditionDate = self._get_document_date()
        documentType = self._get_verifactu_document_type()
        amountTax = self._get_verifactu_amount_tax()
        amountTotal = self._get_verifactu_amount_total()
        previousHash = self._get_verifactu_previous_hash()
        registrationDate = self._get_verifactu_registration_date()
        verifactu_hash_string = (
            f"IDEmisorFactura={issuerID}&"
            f"NumSerieFactura={serialNumber}&"
            f"FechaExpedicionFactura={expeditionDate}&"
            f"TipoFactura={documentType}&"
            f"CuotaTotal={amountTax}&"
            f"ImporteTotal={amountTotal}&"
            f"Huella={previousHash}&"
            f"FechaHoraHusoGenRegistro={registrationDate}"
        )
        return verifactu_hash_string
