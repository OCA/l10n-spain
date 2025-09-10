odoo.define("l10n_es_verifactu_pos_oca.models", function (require) {
    "use strict";

    const {Order} = require("point_of_sale.models");
    const Registries = require("point_of_sale.Registries");

    // eslint-disable-next-line no-shadow
    const VerifactuOrder = (Order) =>
        // eslint-disable-next-line no-shadow
        class VerifactuOrder extends Order {
            export_for_printing() {
                const result = super.export_for_printing(...arguments);
                result.verifactu_qr =
                    this.finalized && this._get_verifactu_qr_code_data();
                return result;
            }

            _build_verifactu_qr_url() {
                const baseUrl = this.pos.config.verifactu_base_url;
                const vatNumber = (this.pos.company.vat || "").replace(/^ES/i, "");
                const date = this.validation_date || this.creation_date;
                const formattedDate = moment(date).format("DD-MM-YYYY");
                const params = new URLSearchParams({
                    nif: vatNumber,
                    numserie: this.l10n_es_unique_id,
                    fecha: formattedDate,
                    importe: this.get_total_with_tax(),
                });
                return `${baseUrl}?${params.toString()}`;
            }

            _get_verifactu_qr_code_data() {
                const isEnabled =
                    this.pos.company.verifactu_enabled &&
                    this.is_simplified_invoice &&
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
            }
        };
    Registries.Model.extend(Order, VerifactuOrder);
});
