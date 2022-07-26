/* Copyright 2021 Binovo IT Human Project SL
   Copyright 2022 Landoo Sistemas de Informacion SL
   Copyright 2022 Advanced Programming Solutions SL (APSL)
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define("l10n_es_ticketbai_pos.ClientListScreen", function (require) {
    "use strict";

    const ClientListScreen = require("point_of_sale.ClientListScreen");
    const Registries = require("point_of_sale.Registries");

    const L10nEsTicketBaiClientListScreen = (ClientListScreen) =>
        class extends ClientListScreen {
            clickClient(event) {
                if (this.env.pos.company.tbai_enabled) {
                    var customer = this.env.pos.db.get_partner_by_id(
                        event.detail.client.id
                    );
                    var order = this.env.pos.get_order();
                    var res = true;

                    if (!order.check_customer_country_code(customer)) {
                        res = false;
                        this.showPopup("ErrorPopup", {
                            title: this.env._t("TicketBAI"),
                            body: _.str.sprintf(
                                this.env._t("Please set Country for customer %s."),
                                customer.name
                            ),
                        });
                    } else if (
                        !order.check_simplified_invoice_spanish_customer(customer)
                    ) {
                        res = false;
                        this.showPopup("ErrorPopup", {
                            title: this.env._t("TicketBAI"),
                            body: this.env._t(
                                "Non spanish customers are not supported for Simplified Invoice."
                            ),
                        });
                    } else if (!order.check_customer_vat(customer)) {
                        res = false;
                        this.showPopup("ErrorPopup", {
                            title: this.env._t("TicketBAI"),
                            body: _.str.sprintf(
                                this.env._t(
                                    "Please set VAT or TicketBAI Partner Identification Number for customer %s."
                                ),
                                customer.name
                            ),
                        });
                    }
                    if (res) {
                        super.clickClient(event);
                    }
                }
            }
        };
    Registries.Component.extend(ClientListScreen, L10nEsTicketBaiClientListScreen);
    return ClientListScreen;
});
