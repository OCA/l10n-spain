odoo.define("l10n_es_pos_by_device.models", function (require) {
    "use strict";

    const {ConnectionLostError} = require("@web/core/network/rpc_service");
    const {Gui} = require("point_of_sale.Gui");

    var models = require("point_of_sale.models");

    var pos_super = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        _set_simplified_invoice_number(config) {
            if (!this.config.pos_sequence_by_device) {
                pos_super._set_simplified_invoice_number.apply(this, arguments);
            } else {
                this.get_device().device_simplified_invoice_number =
                    config.device_simplified_invoice_number;
            }
        },
        _get_simplified_invoice_number() {
            if (!this.config.pos_sequence_by_device) {
                return pos_super._get_simplified_invoice_number.apply(this, arguments);
            }
            return (
                this.get_device().device_simplified_invoice_prefix +
                this.get_padding_simple_inv(
                    this.get_device().device_simplified_invoice_number,
                    this.get_device().device_simplified_invoice_padding
                )
            );
        },
        get_simple_inv_next_number: function () {
            if (!this.env.pos.config.pos_sequence_by_device) {
                return pos_super.get_simple_inv_next_number.apply(this, arguments);
            }
            // If we had pending orders to sync we want to avoid getting the next number
            // from the DB as we'd be ovelaping the sequence.
            if (this.env.pos.db.get_orders().length) {
                return Promise.reject(new ConnectionLostError());
            }
            return this.rpc({
                method: "search_read",
                domain: [["id", "=", this.env.pos.get_device().id]],
                fields: ["device_simplified_invoice_number"],
                model: "pos.device",
            });
        },
        _update_sequence_number: function () {
            if (!this.env.pos.config.pos_sequence_by_device) {
                pos_super._update_sequence_number.apply(this, arguments);
            } else if (this.get_device()) {
                // If trying to send lost order when starting POS,
                // device can still not be chosen.
                ++this.get_device().device_simplified_invoice_number;
            }
        },
        get_device: function () {
            return this.get("pos_device");
        },
        set_device: async function (device) {
            var ret = await this.rpc({
                method: "lock_device",
                model: "pos.device",
                args: [[device.id]],
            });
            if (ret) {
                this.set("pos_device", device);
                device.locked = true;
            }
            return ret;
        },
        unset_device: async function () {
            const device = this.get("pos_device", false);
            if (device) {
                await this.rpc({
                    method: "unlock_device",
                    model: "pos.device",
                    args: [[device.id]],
                });
                this.set("pos_device", false);
                device.locked = false;
            }
        },
        device_select_popup: async function () {
            if (this.config.pos_sequence_by_device) {
                const list = this.pos_devices.map((pos_device) => {
                    return {
                        id: pos_device.id,
                        item: pos_device,
                        label: pos_device.name,
                        isSelected: false,
                    };
                });
                const {confirmed, payload: device} = await Gui.showPopup(
                    "SelectionPopup",
                    {
                        title: this.env._t("Select Physical Device"),
                        list: list,
                    }
                );

                if (!confirmed) {
                    this.trigger("close-pos");
                }

                var ret = await this.set_device(device);

                if (!ret) {
                    await Gui.showPopup("ErrorPopup", {
                        title: this.env._t("Cannot establish device. Clossing POS."),
                        body: this.env._t(
                            "There was a connection error when trying to establish the device."
                        ),
                    });
                    this.trigger("close-pos");
                }
            }
        },
    });

    var order_super = models.Order.prototype;
    models.Order = models.Order.extend({
        export_as_JSON: function () {
            var res = order_super.export_as_JSON.apply(this, arguments);
            res.device = this.pos.get_device();
            return res;
        },
    });

    models.load_models([
        {
            model: "pos.device",
            fields: [
                "name",
                "sequence",
                "locked",
                "company_id",
                "device_simplified_invoice_prefix",
                "device_simplified_invoice_padding",
                "device_simplified_invoice_number",
            ],
            domain: function (self) {
                return self.config.pos_device_ids.length > 0
                    ? [
                          ["company_id", "=", self.config.company_id[0]],
                          ["id", "in", self.config.pos_device_ids],
                          ["locked", "=", false],
                      ]
                    : [
                          ["company_id", "=", self.config.company_id[0]],
                          ["locked", "=", false],
                      ];
            },
            loaded: function (self, pos_devices) {
                self.pos_devices = pos_devices;
            },
        },
    ]);
});
