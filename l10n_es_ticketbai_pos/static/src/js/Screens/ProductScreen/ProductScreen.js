/* Copyright 2021 Binovo IT Human Project SL
   Copyright 2022 Landoo Sistemas de Informacion SL
   Copyright 2022 Advanced Programming Solutions SL (APSL)
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define("l10n_es_ticketbai_pos.ProductScreen", function (require) {
    "use strict";

    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");

    const L10nEsTicketBaiProductScreen = (OriginProductScreen) =>
        class extends OriginProductScreen {
            async _clickProduct(event) {
                const selectedProduct = event.detail;
                let isValid = true;
                if (this.env.pos.company.tbai_enabled) {
                    if (selectedProduct.taxes_id.length !== 1) {
                        isValid = false;
                        this.showPopup("ErrorPopup", {
                            title: this.env._t("TicketBAI"),
                            body: `${this.env._t("Please set a tax for product")} ${
                                selectedProduct.display_name
                            }.`,
                        });
                    }
                }
                if (isValid) {
                    return await super._clickProduct(event);
                }
            }
        };
    Registries.Component.extend(ProductScreen, L10nEsTicketBaiProductScreen);
    return ProductScreen;
});
