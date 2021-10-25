/* Copyright 2021 Binovo IT Human Project SL
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define('l10n_es_ticketbai_pos.widgets', function (require) {
    'use strict';

    var widgets = require('pos_order_mgmt.widgets');
    var tbai_models = require('l10n_es_ticketbai_pos.tbai_models');

    widgets.OrderListScreenWidget.include({

        order_action: function(order_data, action) {
            var self = this;
            if (order_data.tbai_qr_src) {
                self._super(order_data, action);
            } else {
                self.generate_qr_code(order_data).then(function(src) {
                    order_data.tbai_qr_src = src;
                    self.order_action(order_data, action);
                });
            }
        },

        generate_qr_code: function(order_data) {
            var qr_url = order_data.tbai_qr_url;
            var qr_options = tbai_models.TicketBAISimplifiedInvoice.prototype.qr_options;
            var src = QRCode.toDataURL(qr_url, qr_options).then(function(src) {
                return src;
            });
            return src;
        },

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
