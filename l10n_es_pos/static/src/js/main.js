/**
 * # -*- coding: utf-8 -*-
 * # See README.rst file on addon root folder for license details
 */

// Check jQuery available
if (typeof jQuery === 'undefined') { throw new Error('l10n_es POS Simplified invoice Addon requires jQuery') }

+function ($) {
    'use strict';

    openerp.l10n_es_pos = function (instance) {
        var _t = instance.web._t,
            _lt = instance.web._lt;
        var QWeb = instance.web.qweb;
        var module = instance.point_of_sale;
        var _simplified_limit_get = function() {
            var limit = 3000
            // Get simplified limit from POS config
            if (
                posmodel
                && posmodel.config
                && posmodel.config.simplified_invoice_limit
            ) {
                limit = posmodel.config.simplified_invoice_limit;
            }
            return limit;
        };

        var OrderParent = module.Order;
        module.Order = module.Order.extend({
            initialize: function(attributes){
                OrderParent.prototype.initialize.apply(this, arguments);
                // By default, simplified
                this.simplified = true;
            },
            export_for_printing: function(attributes){
                var order = OrderParent.prototype.export_for_printing.apply(this, arguments);
                order['simplified'] = this.is_simplified();
                return order;
            },
            export_as_JSON: function() {
                var order = OrderParent.prototype.export_as_JSON.apply(this, arguments);
                order['simplified'] = this.is_simplified();
                return order;
            },
            set_simplified: function(simplified) {
                this.simplified = !!simplified;
            },
            is_simplified: function() {
                var limit = _simplified_limit_get();
                var amount_total = this.getTotalTaxIncluded();
                var simplified = this.simplified;
                // If simplified limit raised,
                // then this order can not be simplified
                if (amount_total > limit) {
                    simplified = false
                }
                return simplified;
            },
        });

        instance.web.Widget.include({
            is_button_disabled: function(name){
                var b = this.buttons[name];
                if (b != undefined) {
                    return b.disabled;
                }
                return true;
            },
        });

        // Widget: ScreenWidget
        instance.point_of_sale.PaymentScreenWidget.include({
            invoice_button_check: function() {
                var currentOrder = this.pos.get('selectedOrder');
                var dueTotal = currentOrder.getTotalTaxIncluded();
                var limit = _simplified_limit_get()
                if (this.pos_widget.action_bar ) {
                    if (dueTotal > limit) {
                        this.pos_widget.action_bar.set_button_disabled('validation', true);
                        this.pos_widget.action_bar.set_button_disabled('invoice', !this.is_paid());
                    }
                }
            },
            update_payment_summary: function() {
                var result = this._super.apply(this, arguments);
                this.invoice_button_check()
                return result
            },
            validate_order: function(options) {
                var currentOrder = this.pos.get('selectedOrder');
                var result;
                options = options || {};
                if (options.invoice) {
                    // Check for client
                    if (!currentOrder.get_client()) {
                        this.pos_widget.screen_selector.show_popup('error',{
                            message: _t('An anonymous order cannot be invoiced'),
                            comment: _t('Please select a client for this order. This can be done by clicking the order tab'),
                        });
                        return;
                    }
                    // Set this order as not simplified even if no limit raised
                    currentOrder.set_simplified(false)
                    // Disable standard invoice flow
                    options.invoice = false
                }
                result = this._super.apply(this, arguments);
                this.invoice_button_check()
                return result
            },
        });

    };


}(jQuery);
