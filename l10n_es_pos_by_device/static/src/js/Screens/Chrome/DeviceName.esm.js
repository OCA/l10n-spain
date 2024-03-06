/** @odoo-module **/

import PosComponent from "point_of_sale.PosComponent";
import Registries from "point_of_sale.Registries";

export class DeviceName extends PosComponent {
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
