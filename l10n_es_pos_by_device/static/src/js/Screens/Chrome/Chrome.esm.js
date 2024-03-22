/** @odoo-module **/

import Chrome from "point_of_sale.Chrome";
import Registries from "point_of_sale.Registries";

export const L10nEsPosChrome = (OriginalChrome) =>
    class extends OriginalChrome {
        async start() {
            await super.start();
            if (this.env.pos.config.pos_sequence_by_device) {
                const list = this.env.pos.pos_devices.map((pos_device) => {
                    return {
                        id: pos_device.id,
                        item: pos_device,
                        label: pos_device.name,
                        isSelected: false,
                    };
                });
                const {confirmed, payload: device} = await this.showPopup(
                    "SelectionPopup",
                    {
                        title: this.env._t("Select Physical Device"),
                        list: list,
                    }
                );

                if (!confirmed) {
                    this.trigger("close-pos");
                    return;
                }

                const ret = await this.env.pos.set_device(device);

                if (!ret) {
                    await this.showPopup("ErrorPopup", {
                        title: this.env._t("Cannot establish device. Clossing POS."),
                        body: this.env._t(
                            "There was a connection error when trying to establish the device."
                        ),
                    });
                    this.trigger("close-pos");
                }
            }
        }
        async _closePos() {
            if (this.env.pos.config.pos_sequence_by_device) {
                await this.env.pos.unset_device();
            }
            await super._closePos();
        }
    };

Registries.Component.extend(Chrome, L10nEsPosChrome);
