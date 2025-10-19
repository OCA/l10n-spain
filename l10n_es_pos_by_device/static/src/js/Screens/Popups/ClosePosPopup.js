odoo.define("l10n_es_pos_by_device.ClosePosPopup", function (require) {
    "use strict";

    const ClosePosPopup = require("point_of_sale.ClosePosPopup");
    const Registries = require("point_of_sale.Registries");

    const PosByDeviceClosePopup = (ClosePosPopup) =>
        class extends ClosePosPopup {
            async closeSession() {
                if (
                    this.env.pos.config.pos_sequence_by_device &&
                    this.canCloseSession()
                ) {
                    this.env.pos.unset_device();
                }
                return super.closeSession();
            }
        };

    Registries.Component.extend(ClosePosPopup, PosByDeviceClosePopup);

    return ClosePosPopup;
});
