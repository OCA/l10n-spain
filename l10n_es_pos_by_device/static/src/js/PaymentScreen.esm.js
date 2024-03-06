/** @odoo-module **/

import PaymentScreen from "l10n_es_pos.PaymentScreen";
import Registries from "point_of_sale.Registries";

export const L10nEsPosByDevicePaymentScreen = (OriginalPaymentScreen) =>
    class extends OriginalPaymentScreen {
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
