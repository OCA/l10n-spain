odoo.define("l10n_es_pos.chrome", function (require) {
    "use strict";

    const Chrome = require("point_of_sale.Chrome");
    const Registries = require("point_of_sale.Registries");

    const L10nEsPosChrome = (Chrome) =>
        class extends Chrome {
            async start() {
                await super.start();
                await this.env.pos.device_select_popup();
            }
            async _closePos() {
                if (this.env.pos.config.pos_sequence_by_device) {
                    this.env.pos.unset_device();
                }
                await super._closePos();
            }
            async closeSession() {
                if (this.env.pos.config.pos_sequence_by_device) {
                    this.env.pos.unset_device();
                }
                await super._closePos();
            }
        };

    Registries.Component.extend(Chrome, L10nEsPosChrome);

    return Chrome;
});
