odoo.define("l10n_es_pos.TicketScreen", function (require) {
    "use strict";

    const TicketScreen = require("point_of_sale.TicketScreen");
    const Registries = require("point_of_sale.Registries");

    const L10nEsPosTicketScreen = (TicketScreen) =>
        class extends TicketScreen {
            _getSearchFields() {
                const fields = super._getSearchFields();
                fields.SIMPLIFIED_INVOICE = {
                    repr: (order) => order.name,
                    displayName: this.env._t("Simplified Invoice"),
                    modelField: "l10n_es_unique_id",
                };
                return fields;
            }
        };
    Registries.Component.extend(TicketScreen, L10nEsPosTicketScreen);
    return TicketScreen;
});
