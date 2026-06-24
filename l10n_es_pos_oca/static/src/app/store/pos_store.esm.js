/* Copyright 2016 David Gómez Quilón <david.gomez@aselcis.com>
   Copyright 2018-19 Tecnativa - David Vidal
   Copyright 2024 (APSL-Nagarro) - Antoni Marroig
   Copyright 2025 Alia Technologies - César Parguiñas
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

import {ConnectionLostError} from "@web/core/network/rpc";
import {PosStore} from "@point_of_sale/app/store/pos_store";
import {patch} from "@web/core/utils/patch";

patch(PosStore.prototype, {
    /**
     * Gets the padded simplified invoice number.
     * @param number
     * @param padding
     * @returns {*}
     * @private
     */
    _getPaddingSimpleInv(number, padding) {
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

    /**
     * Sets the simplified invoice number in the config.
     * @param l10n_es_simplified_invoice_number
     */
    setSimplifiedInvoiceNumber(l10n_es_simplified_invoice_number) {
        this.config.l10n_es_simplified_invoice_number =
            l10n_es_simplified_invoice_number;
    },

    /**
     * Gets the current simplified invoice number from the config.
     * @returns {number|*}
     */
    getCurrentSimplifiedInvoiceNumber() {
        return this.config.l10n_es_simplified_invoice_number;
    },

    /**
     * Generates the simplified unique ID for the current invoice.
     * @returns {String}
     */
    getSimplifiedUniqueId() {
        return (
            this.config.l10n_es_simplified_invoice_prefix +
            this._getPaddingSimpleInv(
                this.config.l10n_es_simplified_invoice_number,
                this.config.l10n_es_simplified_invoice_padding
            )
        );
    },

    /**
     * Increments the simplified invoice number in the config.
     */
    incrementSimplifiedInvoiceNumber() {
        this.config.l10n_es_simplified_invoice_number += 1;
    },

    /**
     * Checks if there are pending orders to be synced.
     * @returns {Boolean}
     */
    hasPendingOrders() {
        const {orderToCreate, orderToUpdate} = this.getPendingOrder();
        return orderToCreate.length + orderToUpdate.length > 0;
    },

    /**
     * Gets the next simplified invoice number, taking into account pending orders.
     * @returns {Promise<number|*>}
     */
    async getSimpleInvNextNumber() {
        // First, get the next number from the DB to be sure we have the latest
        try {
            if (this.config.prevent_offline_validation) {
                // Execute pos.l10n_es_simplified_invoice_sequence_id.next_by_id() directly
                // as on this mode there should be no pending orders
                var l10n_es_simplified_invoice_number = await this.data.call(
                    "pos.config",
                    "next_l10n_es_sequence_number",
                    [this.config.id],
                    {}
                );
            } else {
                const config = await this.data.searchRead(
                    "pos.config",
                    [["id", "=", this.config.id]],
                    ["l10n_es_simplified_invoice_number"]
                );

                var l10n_es_simplified_invoice_number =
                    config[0]?.l10n_es_simplified_invoice_number || 1;
            }

            this.config.l10n_es_simplified_invoice_number =
                l10n_es_simplified_invoice_number || 1;
        } catch (error) {
            // Throw error if it's a connection lost error and we want to prevent offline validation
            if (
                error instanceof ConnectionLostError &&
                this.config.prevent_offline_validation
            ) {
                throw error;
            }
            // Offline -> First time connection lost no has pending orders, we can increment the number
            if (!this.hasPendingOrders()) {
                this.incrementSimplifiedInvoiceNumber();
            }
            console.error(error);
        }

        if (this.hasPendingOrders()) {
            const {orderToCreate} = this.getPendingOrder();

            // Prevent overlapping by calculating the max number in pending orders when lost connection
            const simplifiedInvNumFromOrderPending =
                Math.max(...orderToCreate.map((o) => o.l10n_es_simplified_number)) + 1;

            // Set the next number to be at least the max from pending orders
            if (
                this.config.l10n_es_simplified_invoice_number <
                simplifiedInvNumFromOrderPending
            ) {
                this.config.l10n_es_simplified_invoice_number =
                    simplifiedInvNumFromOrderPending;
            }
        }

        return this.config.l10n_es_simplified_invoice_number;
    },

    /**
     * Extends receipt header data with simplified invoice info.
     * @override
     * @param order
     * @returns {*}
     */
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
});
