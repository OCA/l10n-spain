/* Copyright 2018 Tecnativa - David Vidal
   License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */
odoo.define('l10n_es_pos_order_mgmt.widgets', function (require) {
    "use strict";

    var screens = require('pos_order_mgmt.widgets');

    screens.OrderListScreenWidget.include({
        _prepare_order_from_order_data: function (order_data) {
            var order = this._super(order_data);
            if (!order_data.simplified_invoice) {
                return order;
            }
            if (order_data.return) {
                order.origin_simplified_invoice = order_data.simplified_invoice;
            } else {
                order.simplified_invoice = order_data.simplified_invoice;
                order.origin_simplified_invoice = order_data.origin_simplified_invoice;
            }
            return order;
        },
    });

});
