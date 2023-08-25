odoo.define("l10n_es_pos_sii.models", function (require) {
    "use strict";

    const {Order} = require("point_of_sale.models");
    const Registries = require("point_of_sale.Registries");

    // eslint-disable-next-line no-shadow
    const OverloadOrder = (Order) =>
        // eslint-disable-next-line no-shadow
        class OverloadOrder extends Order {
            init_from_JSON(json) {
                super.init_from_JSON(...arguments);
                this.siiSessionClosed = json.sii_session_closed;
            }
        };

    Registries.Model.extend(Order, OverloadOrder);
});
