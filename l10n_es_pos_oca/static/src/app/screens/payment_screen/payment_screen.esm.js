/** @odoo-module */

/* Copyright 2016 David Gómez Quilón <david.gomez@aselcis.com>
   Copyright 2018 Tecnativa - David Vidal
   Copyright 2020 Tecnativa - João Marques
   Copyright 2024 (APSL-Nagarro) - Antoni Marroig
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

import {PaymentScreen} from "@point_of_sale/app/screens/payment_screen/payment_screen";
import {patch} from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        const below_limit =
            this.currentOrder.get_total_with_tax() <=
            this.pos.config.l10n_es_simplified_invoice_limit;
        if (this.pos.config.is_simplified_config) {
            const order = this.currentOrder;
            if (below_limit && !order.to_invoice) {
                await order.set_simple_inv_number();
            } else {
                // Force invoice above limit. Online is needed.
                order.to_invoice = true;
            }
            order.partner =
                order.partner ||
                this.pos.db.partner_by_id[this.pos.config.simplified_partner_id[0]];
        }
        await super.validateOrder(isForceValidate);
    },
});
