/* Copyright 2016 David Gómez Quilón <david.gomez@aselcis.com>
   Copyright 2018 Tecnativa - David Vidal
   Copyright 2020 Tecnativa - João Marques
   Copyright 2024 (APSL-Nagarro) - Antoni Marroig
   Copyright 2025 Alia Technologies - César Parguiñas
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

import {ConnectionLostError} from "@web/core/network/rpc";
import {PaymentScreen} from "@point_of_sale/app/screens/payment_screen/payment_screen";
import {patch} from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    /**
     * Validates the order, setting simplified invoice numbers if applicable.
     * @override
     * @param isForceValidate
     * @returns {Promise<void>}
     */
    async validateOrder(isForceValidate) {
        const below_limit =
            this.currentOrder.get_total_with_tax() <=
            this.pos.config.l10n_es_simplified_invoice_limit;

        if (this.pos.config.is_simplified_config) {
            const order = this.currentOrder;
            if (below_limit && !order.to_invoice) {
                await this.setSimpleInvNumber();
            } else {
                // Force invoice above limit. Online is needed.
                order.to_invoice = true;
            }
        }
        await super.validateOrder(isForceValidate);
    },

    /**
     * Sets the simplified invoice number for the current order.
     * @returns {Promise<void>}
     */
    async setSimpleInvNumber() {
        try {
            const l10n_es_simplified_invoice_number =
                await this.pos.getSimpleInvNextNumber();
            this.pos.setSimplifiedInvoiceNumber(l10n_es_simplified_invoice_number);
        } catch (error) {
            if ((!error) instanceof ConnectionLostError) {
                throw error;
            }
        } finally {
            const order = this.currentOrder;
            order.update({
                l10n_es_simplified_number: this.pos.getCurrentSimplifiedInvoiceNumber(),
                l10n_es_unique_id: this.pos.getSimplifiedUniqueId(),
                is_l10n_es_simplified_invoice: true,
            });
        }
    },
});
