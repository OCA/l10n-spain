/** @odoo-module */

/* Copyright 2016 David Gómez Quilón <david.gomez@aselcis.com>
   Copyright 2018-19 Tecnativa - David Vidal
   Copyright 2024 (APSL-Nagarro) - Antoni Marroig
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

import {ConnectionLostError} from "@web/core/network/rpc_service";
import {PosStore} from "@point_of_sale/app/store/pos_store";
import {patch} from "@web/core/utils/patch";

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        this.pushed_simple_invoices = [];
        // Unique UUID
        this.own_simplified_invoice_prefix = "";
    },
    get_simple_inv_next_number() {
        // If we had pending orders to sync we want to avoid getting the next number
        // from the DB as we'd be ovelaping the sequence.
        if (this.db.get_orders().length) {
            return Promise.reject(new ConnectionLostError());
        }
        return this.orm.searchRead(
            "pos.config",
            ["id", "=", this.config.id],
            ["l10n_es_simplified_invoice_number"]
        );
    },
    get_padding_simple_inv(number, padding) {
        var diff = padding - number.toString().length;
        let result = "";
        if (diff <= 0) {
            result = number;
        } else {
            for (let i = 0; i < diff; i++) {
                result += "0";
            }
            result += number;
        }
        return result;
    },
    _update_sequence_number() {
        ++this.config.l10n_es_simplified_invoice_number;
    },
    push_simple_invoice(order) {
        if (this.pushed_simple_invoices.indexOf(order.data.l10n_es_unique_id) === -1) {
            this.pushed_simple_invoices.push(order.data.l10n_es_unique_id);
            this._update_sequence_number();
        }
    },
    async _flush_orders(orders) {
        var self = this;
        // Save pushed orders numbers
        orders.forEach((order) => {
            if (!order.data.to_invoice) {
                self.push_simple_invoice(order);
            }
        });
        return await super._flush_orders(...arguments);
    },
    _set_simplified_invoice_number(config) {
        this.config.l10n_es_simplified_invoice_number =
            config.l10n_es_simplified_invoice_number;
    },
    _get_simplified_invoice_number() {
        return (
            this.config.l10n_es_simplified_invoice_prefix +
            this.get_padding_simple_inv(
                this.config.l10n_es_simplified_invoice_number,
                this.config.l10n_es_simplified_invoice_padding
            )
        );
    },
    getReceiptHeaderData(order) {
        const result = super.getReceiptHeaderData(...arguments);
        if (order) {
            result.is_simplified_config = this.config.is_simplified_config;
            result.partner = order.get_partner();
            result.l10n_es_unique_id = order.l10n_es_unique_id;
            result.to_invoice = order.to_invoice;
        }
        return result;
    },
    _getCreateOrderContext(orders) {
        let context = super._getCreateOrderContext(...arguments);
        const noOrderPrinting = orders.every(
            (order) => !order.to_invoice && order.data.is_simplified_config
        );
        if (noOrderPrinting) {
            context = {...context, generate_pdf: false};
        }
        return context;
    },
});
