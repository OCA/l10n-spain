odoo.define("l10n_es_pos.DeviceName", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");

    class DeviceName extends PosComponent {
        get devicename() {
            const device = this.env.pos.get_device();
            if (device) {
                return device.name;
            }
            return this.env._t("No device");
        }
    }
    DeviceName.template = "DeviceName";

    Registries.Component.add(DeviceName);

    return DeviceName;
});
