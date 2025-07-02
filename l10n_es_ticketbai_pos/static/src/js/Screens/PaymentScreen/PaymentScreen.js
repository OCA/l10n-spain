/* Copyright 2021 Binovo IT Human Project SL
   Copyright 2022 Landoo Sistemas de Informacion SL
   Copyright 2022 Advanced Programming Solutions SL (APSL)
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define("l10n_es_ticketbai_pos.PaymentScreen", function (require) {
    "use strict";

    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const Registries = require("point_of_sale.Registries");

    const L10nEsTicketBaiPaymentScreen = (OriginalPaymentScreen) =>
        class extends OriginalPaymentScreen {
            async _isOrderValid() {
                const _t = this.env._t;
                if (this.env.pos.company.tbai_enabled) {
                    const error_msgs = [];
                    const order = this.currentOrder;
                    if (!this.env.pos.tbai_signer) {
                        error_msgs.push(_t("TicketBAI certificate not loaded!"));
                    }
                    if (!order.check_company_vat()) {
                        error_msgs.push(_t("Please set Company VAT."));
                    }
                    if (!order.check_simplified_invoice_spanish_partner()) {
                        error_msgs.push(
                            _t(
                                "Non spanish customers are not supported for Simplified Invoice."
                            )
                        );
                    }
                    if (!order.check_partner_vat()) {
                        error_msgs.push(
                            _t(
                                "Please set VAT or TicketBAI Partner Identification Number for customer."
                            )
                        );
                    }
                    if (!order.check_fiscal_position_vat_regime_key()) {
                        error_msgs.push(
                            _t(
                                `Please set VAT Regime Key for fiscal position ${order.fiscal_position.name}.`
                            )
                        );
                    }
                    if (!order.check_products_have_taxes()) {
                        error_msgs.push(
                            _t("At least one product does not have a tax.")
                        );
                    }
                    if (
                        !order.tbai_current_invoice ||
                        order.tbai_current_invoice.state() !== "resolved"
                    ) {
                        error_msgs.push(
                            _t("TicketBAI Invoice not built yet. Please try again.")
                        );
                    }
                    if (error_msgs.length) {
                        this.showPopup("ErrorPopup", {
                            title: _t("TicketBAI"),
                            body: error_msgs.join("\n"),
                        });
                        return false;
                    }
                }
                return await super._isOrderValid(...arguments);
            }

            async validateOrder() {
                const order = this.currentOrder;
                if (this.env.pos.company.tbai_enabled && !order.is_to_invoice()) {
                    if (!order.tbai_simplified_invoice) {
                        try {
                            await order.tbai_build_invoice();
                            order.tbai_simplified_invoice =
                                await order.tbai_current_invoice;
                        } catch (error) {
                            console.error(
                                "Error while fetching tbai_current_invoice:",
                                error
                            );
                            // Handle the error appropriately, e.g., show a popup or set a default value
                        }
                    }
                }
                await super.validateOrder(...arguments);
            }
        };
    Registries.Component.extend(PaymentScreen, L10nEsTicketBaiPaymentScreen);
    return PaymentScreen;
});
