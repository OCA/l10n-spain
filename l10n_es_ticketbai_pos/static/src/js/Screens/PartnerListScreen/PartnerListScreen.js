/* Copyright 2021 Binovo IT Human Project SL
   Copyright 2022 Landoo Sistemas de Informacion SL
   Copyright 2022 Advanced Programming Solutions SL (APSL)
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define("l10n_es_ticketbai_pos.PartnerListScreen", function (require) {
    "use strict";

    const PartnerListScreen = require("point_of_sale.PartnerListScreen");
    const Registries = require("point_of_sale.Registries");

    const L10nEsTicketBaiPartnerListScreen = (OriginalPartnerListScreen) =>
        class extends OriginalPartnerListScreen {
            clickPartner(partner) {
                if (this.env.pos.company.tbai_enabled) {
                    const order = this.currentOrder;
                    let isSuccessful = true;
                    const currentPartner = partner || order.get_partner();

                    if (!order.check_partner_country_code(currentPartner)) {
                        isSuccessful = false;
                        this.showPopup("ErrorPopup", {
                            title: this.env._t("TicketBAI"),
                            body: _.str.sprintf(
                                this.env._t("Please set Country for customer %s."),
                                currentPartner.name
                            ),
                        });
                    } else if (
                        !order.check_simplified_invoice_spanish_partner(currentPartner)
                    ) {
                        isSuccessful = false;
                        this.showPopup("ErrorPopup", {
                            title: this.env._t("TicketBAI"),
                            body: this.env._t(
                                "Non spanish customers are not supported for Simplified Invoice."
                            ),
                        });
                    } else if (!order.check_partner_vat(currentPartner)) {
                        isSuccessful = false;
                        this.showPopup("ErrorPopup", {
                            title: this.env._t("TicketBAI"),
                            body: _.str.sprintf(
                                this.env._t(
                                    "Please set VAT or TicketBAI Partner Identification Number for customer %s."
                                ),
                                currentPartner.name
                            ),
                        });
                    }
                    if (isSuccessful) {
                        return super.clickPartner(currentPartner);
                    }
                }
            }
        };
    Registries.Component.extend(PartnerListScreen, L10nEsTicketBaiPartnerListScreen);
    return PartnerListScreen;
});
