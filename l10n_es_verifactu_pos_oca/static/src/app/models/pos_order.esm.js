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
     * Build the Verifactu QR URL with required parameters
     * @returns {String} The complete URL for the QR code
     */
    _build_verifactu_qr_url() {
        const baseUrl = this.config.verifactu_base_url;
        const vatNumber = (this.company.vat || "").replace(/^ES/i, "");
        const date = this.date_order || this.create_date;
        const isoDate = date.replace(" ", "T");
        const formattedDate = luxon.DateTime.fromISO(isoDate).toFormat("dd-MM-yyyy");
        const params = new URLSearchParams({
            nif: vatNumber,
            numserie: this.l10n_es_unique_id,
            fecha: formattedDate,
            importe: this.get_total_with_tax(),
        });
        return `${baseUrl}?${params.toString()}`;
    },

    /**
     * Generate QR code data in SVG format for Verifactu
     * @returns {string|boolean} Base64 encoded SVG QR code or false if disabled
     */
    _get_verifactu_qr_code_data() {
        const isEnabled =
            this.verifactu_enabled &&
            this.is_l10n_es_simplified_invoice &&
            (!this.fiscal_position ||
                (this.fiscal_position && this.fiscal_position.aeat_active));

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
