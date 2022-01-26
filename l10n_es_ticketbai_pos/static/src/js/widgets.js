/* Copyright 2021 Binovo IT Human Project SL
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define('l10n_es_ticketbai_pos.widgets', function (require) {
    'use strict';

    var widgets = require('pos_order_mgmt.widgets');
    var tbai_models = require('l10n_es_ticketbai_pos.tbai_models');

    widgets.OrderListScreenWidget.include({
        _prepare_order_from_order_data: function (order_data) {
            var order = this._super(order_data);
            if (this.pos.company.tbai_enabled) {
                order.tbai_simplified_invoice = new tbai_models.TicketBAISimplifiedInvoice({}, {
                    pos: this.pos,
                    order: order,
                    tbai_identifier: order_data.tbai_identifier,
                    tbai_qr_src: order_data.tbai_qr_src,
                });
            }
            return order;
        },
    });
});
