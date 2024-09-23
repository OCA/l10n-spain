/** @odoo-module */

/* Copyright 2016 David Gómez Quilón <david.gomez@aselcis.com>
   Copyright 2018-19 Tecnativa - David Vidal
   Copyright 2024 (APSL-Nagarro) - Antoni Marroig
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

import {ConnectionLostError} from "@web/core/network/rpc_service";
import {Order} from "@point_of_sale/app/store/models";
import {patch} from "@web/core/utils/patch";

patch(Order.prototype, {
    get_total_with_tax() {
        const total = super.get_total_with_tax(...arguments);
        const below_limit = total <= this.pos.config.l10n_es_simplified_invoice_limit;
        this.is_simplified_invoice =
            below_limit && this.pos.config.is_simplified_config;
        return total;
    },
    set_simple_inv_number() {
        return this.pos
            .get_simple_inv_next_number()
            .then(([config]) => {
                // We'll get the number from DB only when we're online. Otherwise
                // the sequence will run on the client side until the orders are
                // synced.
                this.pos._set_simplified_invoice_number(config);
            })
            .catch((error) => {
                // We'll only consider network errors
                if (!error instanceof ConnectionLostError) {
                    throw error;
                }
            })
            .finally(() => {
                const simplified_invoice_number =
                    this.pos._get_simplified_invoice_number();
                this.l10n_es_unique_id = simplified_invoice_number;
                this.is_simplified_invoice = true;
            });
    },
    get_base_by_tax() {
        const base_by_tax = {};
        this.get_orderlines().forEach(function (line) {
            const tax_detail = line.get_tax_details();
            const base_price = line.get_price_without_tax();
            if (tax_detail) {
                Object.keys(tax_detail).forEach(function (tax) {
                    if (Object.keys(base_by_tax).includes(tax)) {
                        base_by_tax[tax] += base_price;
                    } else {
                        base_by_tax[tax] = base_price;
                    }
                });
            }
        });
        return base_by_tax;
    },
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.to_invoice = json.to_invoice;
        this.l10n_es_unique_id = json.l10n_es_unique_id;
    },
    export_as_JSON() {
        const res = super.export_as_JSON(...arguments);
        res.to_invoice = this.is_to_invoice();
        if (!res.to_invoice) {
            res.l10n_es_unique_id = this.l10n_es_unique_id;
        }
        return res;
    },
    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        result.l10n_es_unique_id = this.l10n_es_unique_id;
        result.is_simplified_config = this.pos.config.is_simplified_config;
        result.to_invoice = this.to_invoice;
        const base_by_tax = this.get_base_by_tax();
        for (const tax of result.tax_details) {
            tax.base = base_by_tax[tax.tax.id];
        }
        return result;
    },
});
