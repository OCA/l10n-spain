/* Copyright 2016 David Gómez...
   Copyright 2025 Alia Technologies - César Parguiñas
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

import {PosOrder} from "@point_of_sale/app/models/pos_order";
import {patch} from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    /**
     * Calculates the base amounts for each tax in the order.
     * @returns {{}}
     */
    getBaseByTax() {
        const base_by_tax = {};
        this.get_orderlines().forEach(function (line) {
            const tax_detail = line.get_tax_details();
            const base_price = line.get_price_without_tax();
            if (tax_detail) {
                Object.keys(tax_detail).forEach(function (tax) {
                    if (Object.prototype.hasOwnProperty.call(base_by_tax, tax)) {
                        base_by_tax[tax] += base_price;
                    } else {
                        base_by_tax[tax] = base_price;
                    }
                });
            }
        });
        return base_by_tax;
    },

    /**
     * Initializes the order from JSON, including simplified invoice details.
     * @override
     * @param json
     */
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.to_invoice = json.to_invoice;
        this.l10n_es_unique_id = json.l10n_es_unique_id;
        this.l10n_es_simplified_number = json.l10n_es_simplified_number;
    },

    /**
     * Exports the order as JSON, including simplified invoice details.
     * @override
     * @returns {*}
     */
    export_as_JSON() {
        const res = super.export_as_JSON(...arguments);
        res.to_invoice = this.is_to_invoice();
        if (!res.to_invoice) {
            res.l10n_es_unique_id = this.l10n_es_unique_id;
            res.l10n_es_simplified_number = this.l10n_es_simplified_number;
            res.is_simplified_config = this.config.is_simplified_config;
            res.to_invoice = this.to_invoice;
        }
        return res;
    },

    /**
     * Exports the order for printing, including simplified invoice details.
     * @override
     * @returns {*}
     */
    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        result.l10n_es_unique_id = this.l10n_es_unique_id;
        result.l10n_es_simplified_number = this.l10n_es_simplified_number;
        result.is_simplified_config = this.config.is_simplified_config;
        result.to_invoice = this.to_invoice;

        const base_by_tax = this.getBaseByTax();
        for (const tax of result.tax_details) {
            tax.base = base_by_tax[tax.tax.id];
        }
        return result;
    },
});
