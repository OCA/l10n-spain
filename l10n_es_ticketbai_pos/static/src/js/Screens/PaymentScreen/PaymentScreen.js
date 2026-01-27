/* Copyright 2021 Binovo IT Human Project SL
   Copyright 2022 Landoo Sistemas de Informacion SL
   Copyright 2022 Advanced Programming Solutions SL (APSL)
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define("l10n_es_ticketbai_pos.PaymentScreen", function (require) {
    "use strict";

    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const Registries = require("point_of_sale.Registries");
    const {Gui} = require("point_of_sale.Gui");

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
                    } else if (!order.is_tbai_invoice_ready()) {
                        error_msgs.push(
                            _t("TicketBAI Invoice is incomplete. Please try again.")
                        );
                    }
                    if (error_msgs.length) {
                        Gui.showPopup("ErrorPopup", {
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
                    console.info("[TicketBAI] Starting order validation...");
                    try {
                        // Start/continue building
                        console.info("[TicketBAI] Building/rebuilding invoice...");
                        await order.tbai_build_invoice();
                        const tbai_inv = await order.tbai_current_invoice;

                        if (!tbai_inv) {
                            // Validation failed → BLOCK order and inform user
                            console.error("[TicketBAI] Invoice build returned null");
                            this.showPopup("ErrorPopup", {
                                title: this.env._t("TicketBAI"),
                                body: this.env._t(
                                    "Cannot generate TicketBAI simplified invoice.\n\n" +
                                        "Check:\n" +
                                        "• Company VAT is set\n" +
                                        "• Customer has VAT (or foreign ID)\n" +
                                        "• All products have exactly one tax\n" +
                                        "• Fiscal position has VAT Regime Key"
                                ),
                            });
                            return;
                        }
                        // ← BLOCK validation
                        if (!tbai_inv.datas || !tbai_inv.signature_value) {
                            console.error("[TicketBAI] Invoice incomplete:", {
                                has_datas: Boolean(tbai_inv.datas),
                                has_signature: Boolean(tbai_inv.signature_value),
                            });
                            this.showPopup("ErrorPopup", {
                                title: this.env._t("TicketBAI - Incomplete Invoice"),
                                body: this.env._t(
                                    "The TicketBAI invoice was generated but is missing critical data.\n\n" +
                                        "This may be due to:\n" +
                                        "• Certificate signing failure\n" +
                                        "• Network connectivity issues\n" +
                                        "• Corrupt certificate\n\n" +
                                        "Please try again or contact support."
                                ),
                            });
                            return;
                        }

                        order.tbai_simplified_invoice = tbai_inv;
                        console.info(
                            "[TicketBAI] Invoice validated and assigned successfully"
                        );
                    } catch (err) {
                        console.error("[TicketBAI] Invoice generation failed:", err);
                        this.showPopup("ErrorPopup", {
                            title: this.env._t("TicketBAI - Critical Error"),
                            body: this.env._t(
                                "Failed to generate or sign the TicketBAI invoice.\n\n" +
                                    "Error: %s\n\n" +
                                    "The order cannot be validated without a valid signed ticket.",
                                err.message || err
                            ),
                        });
                        // ← BLOCK validation (required by law)
                        return;
                    }
                }

                await super.validateOrder(...arguments);
            }
        };
    Registries.Component.extend(PaymentScreen, L10nEsTicketBaiPaymentScreen);
    return PaymentScreen;
});
