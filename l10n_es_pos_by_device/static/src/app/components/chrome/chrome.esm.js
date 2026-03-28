import {ask, makeAwaitable} from "@point_of_sale/app/store/make_awaitable_dialog";
import {Chrome} from "@point_of_sale/app/pos_app";
import {SelectionPopup} from "@point_of_sale/app/utils/input_popups/selection_popup";
import {_t} from "@web/core/l10n/translation";
import {onMounted} from "@odoo/owl";
import {patch} from "@web/core/utils/patch";

patch(Chrome.prototype, {
    setup() {
        super.setup(...arguments);
        onMounted(async () => {
            if (!this.pos.config.pos_sequence_by_device) {
                return;
            }
            const devices = this.pos.models["pos.device"].getAll();
            const list = devices.map((device) => ({
                id: device.id,
                item: device,
                label: device.name,
                isSelected: false,
            }));
            const device = await makeAwaitable(this.pos.dialog, SelectionPopup, {
                title: _t("Select Physical Device"),
                list,
            });
            if (!device) {
                await ask(this.pos.dialog, {
                    title: _t("No device selected"),
                    body: _t("A physical device must be selected to use the POS."),
                });
                await this.pos.closePos();
                return;
            }
            const locked = await this.pos.setDevice(device);
            if (!locked) {
                await ask(this.pos.dialog, {
                    title: _t("Cannot establish device. Closing POS."),
                    body: _t(
                        "There was a connection error when trying to establish the device."
                    ),
                });
                await this.pos.closePos();
            }
        });
    },
});
