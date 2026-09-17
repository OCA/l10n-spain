import {PaymentScreen} from "@point_of_sale/app/screens/payment_screen/payment_screen";
import {_t} from "@web/core/l10n/translation";
import {ask} from "@point_of_sale/app/store/make_awaitable_dialog";
import {patch} from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    /**
     * When device-based sequencing is enabled, abort validation if no device
     * is selected (e.g. after a connection error during startup).
     */
    async validateOrder(isForceValidate) {
        if (this.pos.config.pos_sequence_by_device && !this.pos.getDevice()) {
            await ask(this.dialog, {
                title: _t("Cannot establish device. Closing POS."),
                body: _t(
                    "There was a connection error when trying to establish the device."
                ),
            });
            await this.pos.closePos();
            return;
        }
        if (this.pos.config.pos_sequence_by_device) {
            this.currentOrder.pos_device_id = this.pos.getDevice() || false;
        }
        return super.validateOrder(isForceValidate);
    },
});
