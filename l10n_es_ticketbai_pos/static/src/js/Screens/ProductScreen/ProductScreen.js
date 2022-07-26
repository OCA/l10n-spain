/* Copyright 2021 Binovo IT Human Project SL
   Copyright 2022 Landoo Sistemas de Informacion SL
   Copyright 2022 Advanced Programming Solutions SL (APSL)
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define("l10n_es_ticketbai_pos.ProductScreen", function (require) {
    "use strict";

    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");

    const L10nEsTicketBaiProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            _clickProduct(event) {
                const product = event.detail;
                var res = true;
                if (this.env.pos.company.tbai_enabled) {
                    if (product.taxes_id.length !== 1) {
                        res = false;
                        this.showPopup("ErrorPopup", {
                            title: this.env._t("TicketBAI"),
                            body: _.str.sprintf(
                                this.env._t("Please set a tax for product %s."),
                                product.display_name
                            ),
                        });
                    }
                }
                if (res) {
                    super._clickProduct(event);
                }
            }
        };
    Registries.Component.extend(ProductScreen, L10nEsTicketBaiProductScreen);
    return ProductScreen;
});
