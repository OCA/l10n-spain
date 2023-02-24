odoo.define("l10n_es_pos_by_device.PaymentScreen", function (require) {
    "use strict";

    const PaymentScreen = require("l10n_es_pos.PaymentScreen");
    const Registries = require("point_of_sale.Registries");

    const L10nEsPosByDevicePaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            async _finalizeValidation() {
                if (
                    this.env.pos.config.pos_sequence_by_device &&
                    !this.env.pos.get_device()
                ) {
                    await this.showPopup("ErrorPopup", {
                        title: this.env._t("Cannot establish device. Clossing POS."),
                        body: this.env._t(
                            "There was a connection error when trying to establish the device."
                        ),
                    });
                    this.trigger("close-pos");
                } else {
                    super._finalizeValidation();
                }
            }
        };

    Registries.Component.extend(PaymentScreen, L10nEsPosByDevicePaymentScreen);

    return PaymentScreen;
});
