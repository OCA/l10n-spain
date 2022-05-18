/* Copyright 2021 Binovo IT Human Project SL
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define('l10n_es_ticketbai_pos.screens', function (require) {
    'use strict';

    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var _t = core._t;

    screens.ProductScreenWidget.include({
        click_product: function (product) {
            var res = true;
            if (this.pos.company.tbai_enabled) {
                var order = this.pos.get_order();
                if (1 !== product.taxes_id.length) {
                    res = false;
                    this.gui.show_popup('error', {
                        title: _t('TicketBAI'),
                        body: _.str.sprintf(_t('Please set a tax for product %s.'), product.display_name),
                    });
                }
                var company_regime = this.pos.get_tbai_vat_regime_key_code_by_id(
                    this.pos.company.tbai_vat_regime[0]);
                if (company_regime != '01' && res && order.get_orderlines().length > 0) {
                    var lines_with_surcharge = _.filter(order.get_orderlines(), function (line) {
                        return line.product.has_equivalence_surcharge;
                    });
                    if (
                        (lines_with_surcharge.length > 0 && !product.has_equivalence_surcharge) ||
                        (lines_with_surcharge.length == 0 && product.has_equivalence_surcharge)
                    ) {
                        res = false;
                        this.gui.show_popup('error', {
                            title: _t('TicketBAI'),
                            body: _.str.sprintf(
                                _t('There cannot be lines with and without an equivalence or simplified regime surcharge on the same receipt.'),
                                product.display_name
                            )
                        });
                    }
                }
            }
            if (res) {
                this._super(product);
            }
        },
    });

    screens.PaymentScreenWidget.include({
        order_is_valid: function (force_validation) {
            var res = this._super(force_validation);
            if (this.pos.company.tbai_enabled && res === true) {
                var error_msgs = [];
                var order = this.pos.get_order();
                if (this.pos.tbai_signer === null) {
                    res = false;
                    error_msgs.push(_t("TicketBAI certificate not loaded!"));
                }
                if (!order.check_company_vat()) {
                    res = false;
                    error_msgs.push(_t('Please set Company VAT.'));
                }
                if (!order.check_simplified_invoice_spanish_customer()) {
                    res = false;
                    error_msgs.push(_t('Non spanish customers are not supported for Simplified Invoice.'));
                }
                if (!order.check_customer_vat()) {
                    res = false;
                    error_msgs.push(_t('Please set VAT or TicketBAI Partner Identification Number for customer.'));
                }
                if (!order.check_fiscal_position_vat_regime_key()) {
                    res = false;
                    error_msgs.push(_.str.sprintf(_t('Please set VAT Regime Key for fiscal position %s.'), order.fiscal_position.name));
                }
                if (!order.check_products_have_taxes()) {
                    res = false;
                    error_msgs.push(_t('At least one product does not have a tax.'));
                }
                if (order.tbai_current_invoice.state() !== 'resolved') {
                    res = false;
                    error_msgs.push(_t('TicketBAI Invoice not built yet. Please try again.'));
                }
                if (res === false) {
                    this.gui.show_popup('error', {
                        title: _t('TicketBAI'),
                        body: error_msgs.join('\n'),
                    });
                }
            }
            return res;
        },
        validate_order: function(force_validation) {
            var self = this;
            var order = this.pos.get_order();
            if (this.pos.company.tbai_enabled && !order.is_to_invoice()) {
                if (force_validation == 'tbai_inv_up_to_date') {
                    this._super();
                } else {
                    var order = this.pos.get_order();
                    if (order.fiscal_position
                        && this.pos.get_tbai_vat_regime_key_code_by_id(order.fiscal_position.id) != '01'
                    ) {
                        this.gui.show_popup('error', {
                            title: _t('TicketBAI'),
                            body: _t('Regime not supported for simplified receipt.')
                        });
                        return;
                    }
                    order.tbai_build_invoice();
                    order.tbai_current_invoice.then( function(tbai_inv) {
                        order.tbai_simplified_invoice = tbai_inv;
                        self.validate_order('tbai_inv_up_to_date');}
                    );}
            } else {
                this._super();
            }
        },
    });

    screens.ClientListScreenWidget.include({
        line_select: function (event, $line, id) {
            var res = true;
            if (this.pos.company.tbai_enabled) {
                var customer = this.pos.db.get_partner_by_id(id);
                var order = this.pos.get_order();

                if (!order.check_customer_country_code(customer)) {
                    res = false;
                    this.gui.show_popup('error', {
                        title: _t('TicketBAI'),
                        body: _.str.sprintf(_t('Please set Country for customer %s.'), customer.name),
                    });
                } else if (!order.check_simplified_invoice_spanish_customer(customer)) {
                    res = false;
                    this.gui.show_popup('error', {
                        title: _t('TicketBAI'),
                        body: _t('Non spanish customers are not supported for Simplified Invoice.'),
                    });
                } else if (!order.check_customer_vat(customer)) {
                    res = false;
                    this.gui.show_popup('error', {
                        title: _t('TicketBAI'),
                        body: _.str.sprintf(_t('Please set VAT or TicketBAI Partner Identification Number for customer %s.'), customer.name),
                    });
                }
            }
            if (res) {
                this._super(event, $line, id);
            }
        },
    });

});
