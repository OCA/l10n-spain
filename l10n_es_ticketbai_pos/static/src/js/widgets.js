/* Copyright 2021 Binovo IT Human Project SL
   Copyright 2022 Landoo Sistemas de Informacion SL
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define("l10n_es_ticketbai_pos.widgets", function (require) {
    "use strict";

    var screens = require("point_of_sale.OrderManagementScreen");
    var tbai_models = require("l10n_es_ticketbai_pos.tbai_models");

    screens.OrderList.include({
        _prepare_order_from_order_data: function (order_data, action) {
            var order = this._super(order_data, action);
            if (this.pos.company.tbai_enabled) {
                order.tbai_simplified_invoice =
                    new tbai_models.TicketBAISimplifiedInvoice(
                        {},
                        {
                            pos: this.pos,
                            order: order,
                            tbai_identifier: order_data.tbai_identifier,
                            tbai_qr_src: order_data.tbai_qr_src,
                        }
                    );
            }
            return order;
        },
    });
});
