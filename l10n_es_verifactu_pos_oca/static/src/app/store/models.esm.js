/** @odoo-module **/
import {Order} from "@point_of_sale/app/store/models";
import {patch} from "@web/core/utils/patch";

patch(Order.prototype, {
    // @override
    export_for_printing() {
        const objectReceipt = super.export_for_printing();
        objectReceipt.verifactu_qr =
            this.finalized && this._get_verifactu_qr_code_data();
        return objectReceipt;
    },
    _get_verifactu_qr_code_data() {
        const isEnabled =
            this.pos.company.verifactu_enabled &&
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
    _format_to_DD_MM_YYYY(date) {
        const day = String(date.day).padStart(2, "0");
        const month = String(date.month).padStart(2, "0");
        return `${day}-${month}-${date.year}`;
    },
    _build_verifactu_qr_url() {
        const baseUrl = this.pos.config.verifactu_base_url;
        const vatNumber = (this.pos.company.vat || "").replace(/^ES/i, "");
        const date = this.date_order || this.creation_date;
        const formattedDate = this._format_to_DD_MM_YYYY(date);
        const params = new URLSearchParams({
            nif: vatNumber,
            numserie: this.l10n_es_unique_id,
            fecha: formattedDate,
            importe: this.get_total_with_tax(),
        });
        return `${baseUrl}?${params.toString()}`;
    },
});
