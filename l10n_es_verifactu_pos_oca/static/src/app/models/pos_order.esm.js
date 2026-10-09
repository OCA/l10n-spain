/*
   Copyright 2025 Alia Technologies - César Parguiñas
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

import {PosOrder} from "@point_of_sale/app/models/pos_order";
import {patch} from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    /**
     * Exports order data for printing, including Verifactu QR code if applicable.
     * @override
     * @returns {*}
     */
    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        result.verifactu_qr = this.finalized && this._get_verifactu_qr_code_data();
        return result;
    },

    /**
     * The registration dates the document by the UTC date of `date_order`,
     * so the QR code follows it to keep both on the same day for orders
     * around midnight. That day is the UTC one and not the legal one -- see
     * the ROADMAP.
     * @returns {luxon.DateTime}
     */
    _get_verifactu_document_date() {
        return luxon.DateTime.fromSQL(this.date_order || this.create_date, {
            zone: "utc",
        });
    },

    /**
     * Build the Verifactu QR URL with required parameters
     * @returns {String} The complete URL for the QR code
     */
    _build_verifactu_qr_url() {
        const baseUrl = this.config.verifactu_base_url;
        const vatNumber = (this.company.vat || "").replace(/^ES/i, "");
        const params = new URLSearchParams({
            nif: vatNumber,
            numserie: (this.l10n_es_unique_id || "").substring(0, 60),
            fecha: this._get_verifactu_document_date().toFormat("dd-MM-yyyy"),
            importe: this.get_total_with_tax().toFixed(2),
        });
        return `${baseUrl}?${params.toString()}`;
    },

    /**
     * Whether the backend registers this ticket, decided from what the PoS
     * has loaded rather than from the order's `verifactu_enabled`, which is
     * only computed by the server and so is missing until the order syncs --
     * that would leave the QR code out of any ticket printed offline.
     * @returns {Boolean}
     */
    _is_verifactu_ticket() {
        const startDate = this.company.verifactu_start_date;
        const fiscalPosition = this.fiscal_position_id;
        return Boolean(
            this.company.verifactu_enabled &&
                this.config.verifactu_journal_enabled &&
                this.is_l10n_es_simplified_invoice &&
                !this.is_to_invoice() &&
                (!startDate ||
                    this._get_verifactu_document_date().toISODate() >= startDate) &&
                (!fiscalPosition || fiscalPosition.aeat_active)
        );
    },

    /**
     * Generate QR code data in SVG format for Verifactu
     * @returns {string|boolean} Base64 encoded SVG QR code or false if disabled
     */
    _get_verifactu_qr_code_data() {
        const isEnabled = this._is_verifactu_ticket();

        if (isEnabled) {
            const codeWriter = new window.ZXing.BrowserQRCodeSvgWriter();
            const address = this._build_verifactu_qr_url();
            const hints = new Map();
            hints.set(
                window.ZXing.EncodeHintType.ERROR_CORRECTION,
                window.ZXing.QRCodeDecoderErrorCorrectionLevel.M
            );
            // Minimize quiet zone
            hints.set(window.ZXing.EncodeHintType.MARGIN, 0);
            const qr_code_svg = new XMLSerializer().serializeToString(
                codeWriter.write(address, 150, 150, hints)
            );
            return "data:image/svg+xml;base64," + window.btoa(qr_code_svg);
        }
        return false;
    },
});
