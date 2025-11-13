odoo.define("l10n_es_verifactu_pos_oca.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");

    models.load_fields("res.company", ["verifactu_enabled"]);

    var order_super = models.Order.prototype;
    models.Order = models.Order.extend({
        export_for_printing: function () {
            var result = order_super.export_for_printing.apply(this, arguments);
            result.verifactu_qr = this._get_verifactu_qr_code_data();
            return result;
        },
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
        },
        _get_verifactu_qr_code_data() {
            const isEnabled =
                this.pos.company.verifactu_enabled &&
                this.is_simplified_invoice &&
                (!this.fiscal_position ||
                    (this.fiscal_position && this.fiscal_position.aeat_active));
            if (isEnabled) {
                const address = this._build_verifactu_qr_url();
                return address;
            }
            return false;
        },
    });
});
