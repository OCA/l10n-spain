odoo.define("l10n_es_pos_by_device.CashOpeningPopup", function (require) {
    "use strict";

    const CashOpeningPopup = require("point_of_sale.CashOpeningPopup");
    const Registries = require("point_of_sale.Registries");

    const PosByDeviceCashOpeningPopup = (CashOpeningPopup) =>
        class extends CashOpeningPopup {
            async startSession() {
                await super.startSession();
                await this.env.pos.device_select_popup();
            }
        };

    Registries.Component.extend(CashOpeningPopup, PosByDeviceCashOpeningPopup);

    return CashOpeningPopup;
});
