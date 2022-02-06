odoo.define("l10n_es_pos.OrderManagementControlPanel", function (require) {
    "use strict";

    const OrderManagementControlPanel = require("point_of_sale.OrderManagementControlPanel");
    const Registries = require("point_of_sale.Registries");

    const L10nEsPosOrderManagementControlPanel = (OrderManagementControlPanel) =>
        class extends OrderManagementControlPanel {
            get validSearchTags() {
                const tags = super.validSearchTags;

                tags.add("simplified_invoice");
                return tags;
            }
            get fieldMap() {
                const map = super.fieldMap;

                map.simplified_invoice = "l10n_es_unique_id";
                return map;
            }
            get searchFields() {
                const fields = super.searchFields;

                fields.push("l10n_es_unique_id");
                return fields;
            }
        };

    Registries.Component.extend(
        OrderManagementControlPanel,
        L10nEsPosOrderManagementControlPanel
    );

    return L10nEsPosOrderManagementControlPanel;
});
