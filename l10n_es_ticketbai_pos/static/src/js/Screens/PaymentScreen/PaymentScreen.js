/* Copyright 2021 Binovo IT Human Project SL
   Copyright 2022 Landoo Sistemas de Informacion SL
   Copyright 2022 Advanced Programming Solutions SL (APSL)
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define("l10n_esthis.env._ticketbai_pos.PaymentScreen", function (require) {
    "use strict";

    var core = require("web.core");
    var _t = core._t;
    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const Registries = require("point_of_sale.Registries");

    const L10nEsTicketBaiPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            _isOrderValid(isForceValidate) {
                var res = super._isOrderValid(isForceValidate);
                if (this.env.pos.company.tbai_enabled && res === true) {
                    var error_msgs = [];
                    var order = this.env.pos.get_order();
                    if (this.env.pos.tbai_signer === null) {
                        res = false;
                        error_msgs.push(_t("TicketBAI certificate not loaded!"));
                    }
                    if (!order.check_company_vat()) {
                        res = false;
                        error_msgs.push(_t("Please set Company VAT."));
                    }
                    if (!order.check_simplified_invoice_spanish_customer()) {
                        res = false;
                        error_msgs.push(
                            _t(
                                "Non spanish customers are not supported for Simplified Invoice."
                            )
                        );
                    }
                    if (!order.check_customer_vat()) {
                        res = false;
                        error_msgs.push(
                            _t(
                                "Please set VAT or TicketBAI Partner Identification Number for customer."
                            )
                        );
                    }
                    if (!order.check_fiscal_position_vat_regime_key()) {
                        res = false;
                        error_msgs.push(
                            _.str.sprintf(
                                _t("Please set VAT Regime Key for fiscal position %s."),
                                order.fiscal_position.name
                            )
                        );
                    }
                    if (!order.check_products_have_taxes()) {
                        res = false;
                        error_msgs.push(
                            _t("At least one product does not have a tax.")
                        );
                    }
                    if (order.tbai_current_invoice.state() !== "resolved") {
                        res = false;
                        error_msgs.push(
                            _t("TicketBAI Invoice not built yet. Please try again.")
                        );
                    }
                    if (res === false) {
                        this.showPopup("ErrorPopup", {
                            title: _t("TicketBAI"),
                            body: error_msgs.join("\n"),
                        });
                    }
                }
                return res;
            }

            validateOrder(isForceValidate) {
                var self = this;
                var order = this.env.pos.get_order();
                if (this.env.pos.company.tbai_enabled && !order.is_to_invoice()) {
                    if (isForceValidate === "tbai_inv_up_to_date") {
                        super.validateOrder(isForceValidate);
                    } else {
                        order = this.env.pos.get_order();
                        order.tbai_build_invoice();
                        order.tbai_current_invoice.then(function (tbai_inv) {
                            order.tbai_simplified_invoice = tbai_inv;
                            self.validateOrder("tbai_inv_up_to_date");
                        });
                    }
                } else {
                    super.validateOrder(isForceValidate);
                }
            }
        };
    Registries.Component.extend(PaymentScreen, L10nEsTicketBaiPaymentScreen);
    return PaymentScreen;
});
