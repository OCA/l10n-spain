/**
 * # -*- coding: utf-8 -*-
 * # See README.rst file on addon root folder for license details
 */

// Check jQuery available
if (typeof jQuery === 'undefined') { throw new Error('l10n_es POS Simplified invoice Addon requires jQuery'); }

+function ($) {
    'use strict';

    openerp.l10n_es_pos = function (instance) {
        var _t = instance.web._t,
            _lt = instance.web._lt;
        var QWeb = instance.web.qweb;
        var module = instance.point_of_sale;
        var _simplified_limit_get = function() {
            var limit = 3000;
            // Get simplified limit from POS config
            if (posmodel && posmodel.config &&
                posmodel.config.simplified_invoice_limit) {
                limit = posmodel.config.simplified_invoice_limit;
            }
            return limit;
        };

        var _sequence_next = function(seq){
            var idict = {
                'year': moment().format('YYYY'),
                'month': moment().format('MM'),
                'day': moment().format('DD'),
                'y': moment().format('YY')
            };
            var format = function(s, dict){
                s = s || '';
                $.each(dict, function(k, v){
                    s = s.replace('%(' + k + ')s', v);
                });
                return s;
            };
            function pad(n, width, z) {
                z = z || '0';
                n = n + '';
                if (n.length < width) {
                    n = new Array(width - n.length + 1).join(z) + n;
                }
                return n;
            }
            var num = seq.number_next_actual;
            var prefix = format(seq.prefix, idict);
            var suffix = format(seq.suffix, idict);
            seq.number_next_actual += seq.number_increment;

            return prefix + pad(num, seq.padding) + suffix;
        };

        var PosModelParent = module.PosModel;
        module.PosModel = module.PosModel.extend({
            load_server_data: function(){
                var self = this;
                // Load POS sequence object
                self.models.push({
                    model: 'ir.sequence',
                    fields: [],
                    ids:    function(self){ return [self.config.sequence_id[0]]; },
                    loaded: function(self, sequence){ self.pos_order_sequence = sequence[0]; },
                });
                return PosModelParent.prototype.load_server_data.apply(this, arguments);
            },
            push_order: function(order) {
                if (order !== undefined) {
                    order.set({'sequence_ref_number': this.pos_order_sequence.number_next_actual});
                    order.set({'sequence_ref': _sequence_next(this.pos_order_sequence)});
                }
                return PosModelParent.prototype.push_order.call(this, order);
            }
        });

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
                order['sequence_ref'] = this.get('sequence_ref');
                order['sequence_ref_number'] = this.get('sequence_ref_number');
                return order;
            },
            export_as_JSON: function() {
                var order = OrderParent.prototype.export_as_JSON.apply(this, arguments);
                order['simplified'] = this.is_simplified();
                order['sequence_ref'] = this.get('sequence_ref');
                order['sequence_ref_number'] = this.get('sequence_ref_number');
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
                    simplified = false;
                }
                return simplified;
            },
        });

        instance.web.Widget.include({
            is_button_disabled: function(name){
                var b = this.buttons[name];
                if (b !== undefined) {
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
                var limit = _simplified_limit_get();
                if (this.pos_widget.action_bar ) {
                    if (dueTotal > limit) {
                        this.pos_widget.action_bar.set_button_disabled('validation', true);
                        this.pos_widget.action_bar.set_button_disabled('invoice', !this.is_paid());
                    }
                }
            },
            update_payment_summary: function() {
                var result = this._super.apply(this, arguments);
                this.invoice_button_check();
                return result;
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
                    currentOrder.set_simplified(false);
                    // Disable standard invoice flow
                    options.invoice = false;
                }
                result = this._super.apply(this, arguments);
                this.invoice_button_check();
                return result;
            },
        });

    };


}(jQuery);
