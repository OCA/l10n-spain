/* Copyright 2016 David Gómez Quilón <david.gomez@aselcis.com>
   Copyright 2018 Tecnativa - David Vidal
   Copyright 2020 Tecnativa - João Marques
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define("l10n_es_pos.PaymentScreen", function (require) {
    "use strict";

    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const Registries = require("point_of_sale.Registries");

    const L10nEsPosPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            async validateOrder(isForceValidate) {
                var below_limit =
                    this.currentOrder.get_total_with_tax() <=
                    this.env.pos.config.l10n_es_simplified_invoice_limit;
                if (this.env.pos.config.iface_l10n_es_simplified_invoice) {
                    var order = this.currentOrder;
                    if (below_limit && !order.to_invoice) {
                        order.set_simple_inv_number();
                    } else {
                        // Force invoice above limit. Online is needed.
                        order.to_invoice = true;
                    }
                }
                super.validateOrder(isForceValidate);
            }
        };

    Registries.Component.extend(PaymentScreen, L10nEsPosPaymentScreen);

    return PaymentScreen;
});
