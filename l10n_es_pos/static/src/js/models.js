/* Copyright 2016 David Gómez Quilón <david.gomez@aselcis.com>
   Copyright 2018-19 Tecnativa - David Vidal
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define("l10n_es_pos.models", function (require) {
    "use strict";

    var models = require("point_of_sale.models");

    var pos_super = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function () {
            pos_super.initialize.apply(this, arguments);
            this.pushed_simple_invoices = [];
            return this;
        },
        get_simple_inv_next_number: function () {
            // If we had pending orders to sync we want to avoid getting the next number
            // from the DB as we'd be ovelaping the sequence.
            if (this.env.pos.db.get_orders().length) {
                return Promise.reject({message: {code: "pending_orders"}});
            }
            return this.rpc({
                method: "search_read",
                domain: [["id", "=", this.config_id]],
                fields: ["l10n_es_simplified_invoice_number"],
                model: "pos.config",
            });
        },
        get_padding_simple_inv: function (number) {
            var diff =
                this.config.l10n_es_simplified_invoice_padding -
                number.toString().length;
            var result = "";
            if (diff <= 0) {
                result = number;
            } else {
                for (var i = 0; i < diff; i++) {
                    result += "0";
                }
                result += number;
            }
            return result;
        },
        push_simple_invoice: function (order) {
            if (
                this.pushed_simple_invoices.indexOf(order.data.l10n_es_unique_id) === -1
            ) {
                this.pushed_simple_invoices.push(order.data.l10n_es_unique_id);
                ++this.config.l10n_es_simplified_invoice_number;
            }
        },
        _flush_orders: function (orders) {
            var self = this;
            // Save pushed orders numbers
            _.each(orders, function (order) {
                if (!order.data.to_invoice) {
                    self.push_simple_invoice(order);
                }
            });
            return pos_super._flush_orders.apply(this, arguments);
        },
    });

    var order_super = models.Order.prototype;
    models.Order = models.Order.extend({
        get_total_with_tax: function () {
            var total = order_super.get_total_with_tax.apply(this, arguments);
            var below_limit = total <= this.pos.config.l10n_es_simplified_invoice_limit;
            this.is_simplified_invoice =
                below_limit && this.pos.config.iface_l10n_es_simplified_invoice;
            return total;
        },
        set_simple_inv_number: function () {
            return this.pos
                .get_simple_inv_next_number()
                .then(([config]) => {
                    // We'll get the number from DB only when we're online. Otherwise
                    // the sequence will run on the client side until the orders are
                    // synced.
                    this.pos.config.l10n_es_simplified_invoice_number =
                        config.l10n_es_simplified_invoice_number;
                })
                .catch((error) => {
                    // We'll only consider network errors (XmlHttpRequestError) or
                    // forced rejections to resync invoice numbers
                    if (
                        error.message &&
                        ![-32098, "pending_orders"].includes(error.message.code)
                    ) {
                        throw error;
                    }
                })
                .finally(() => {
                    const simplified_invoice_number =
                        this.pos.config.l10n_es_simplified_invoice_prefix +
                        this.pos.get_padding_simple_inv(
                            this.pos.config.l10n_es_simplified_invoice_number
                        );
                    this.l10n_es_unique_id = simplified_invoice_number;
                    this.is_simplified_invoice = true;
                });
        },
        get_base_by_tax: function () {
            var base_by_tax = {};
            this.get_orderlines().forEach(function (line) {
                var tax_detail = line.get_tax_details();
                var base_price = line.get_price_without_tax();
                if (tax_detail) {
                    Object.keys(tax_detail).forEach(function (tax) {
                        if (Object.keys(base_by_tax).includes(tax)) {
                            base_by_tax[tax] += base_price;
                        } else {
                            base_by_tax[tax] = base_price;
                        }
                    });
                }
            });
            return base_by_tax;
        },
        init_from_JSON: function (json) {
            order_super.init_from_JSON.apply(this, arguments);
            this.to_invoice = json.to_invoice;
            this.l10n_es_unique_id = json.l10n_es_unique_id;
        },
        export_as_JSON: function () {
            var res = order_super.export_as_JSON.apply(this, arguments);
            res.to_invoice = this.is_to_invoice();
            if (!res.to_invoice) {
                res.l10n_es_unique_id = this.l10n_es_unique_id;
            }
            return res;
        },
        export_for_printing: function () {
            var result = order_super.export_for_printing.apply(this, arguments);
            var company = this.pos.company;
            result.l10n_es_unique_id = this.l10n_es_unique_id;
            result.to_invoice = this.to_invoice;
            result.company.street = company.street;
            result.company.zip = company.zip;
            result.company.city = company.city;
            result.company.state_id = company.state_id;
            var base_by_tax = this.get_base_by_tax();
            for (const tax of result.tax_details) {
                tax.base = base_by_tax[tax.tax.id];
            }
            return result;
        },
    });

    models.load_fields("res.company", ["street", "city", "state_id", "zip"]);
});
