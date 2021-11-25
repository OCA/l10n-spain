odoo.define("l10n_es_pos.OrderRow", function (require) {
    "use strict";

    const OrderRow = require("point_of_sale.OrderRow");
    const Registries = require("point_of_sale.Registries");

    const L10nEsPosOrderRow = (OrderRow) =>
        class extends OrderRow {
            get simplified_invoice() {
                return this.order.l10n_es_unique_id || "";
            }
        };

    Registries.Component.extend(OrderRow, L10nEsPosOrderRow);

    return OrderRow;
});
