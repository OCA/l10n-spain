import {Component} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {usePos} from "@point_of_sale/app/store/pos_hook";

export class DeviceName extends Component {
    static template = "l10n_es_pos_by_device.DeviceName";
    static props = {};

    setup() {
        this.pos = usePos();
    }

    get deviceName() {
        const device = this.pos.getDevice();
        return device ? device.name : _t("No device");
    }
}
