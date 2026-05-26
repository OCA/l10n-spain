/** @odoo-module */

/* Copyright 2016 David Gómez Quilón <david.gomez@aselcis.com>
   Copyright 2018 Tecnativa - David Vidal
   Copyright 2020 Tecnativa - João Marques
   Copyright 2024 (APSL-Nagarro) - Antoni Marroig
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

import {ErrorPopup} from "@point_of_sale/app/errors/popups/error_popup";
import {ConnectionLostError} from "@web/core/network/rpc_service";
import {PaymentScreen} from "@point_of_sale/app/screens/payment_screen/payment_screen";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        const below_limit =
            this.currentOrder.get_total_with_tax() <=
            this.pos.config.l10n_es_simplified_invoice_limit;
        if (this.pos.config.is_simplified_config) {
            const order = this.currentOrder;
            if (below_limit && !order.to_invoice) {
                try {
                    await order.set_simple_inv_number();
                } catch (error) {
                    if (
                        error instanceof ConnectionLostError &&
                        this.pos.config.prevent_offline_validation
                    ) {
                        this.popup.add(ErrorPopup, {
                            title: _t("Connection Lost"),
                            body: _t(
                                "Cannot validate the order without connection. This may be due to a lost connection or the server being unreachable at this moment. Please reconnect and try again."
                            ),
                        });
                        return false;
                    }
                }
            } else {
                // Force invoice above limit. Online is needed.
                order.to_invoice = true;
            }
        }
        await super.validateOrder(isForceValidate);
    },
});
