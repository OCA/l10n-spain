/* Copyright 2019 Solvos Consultoría Informática
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define('l10n_es_pos_product_discount.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');

    var orderline_super = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({

        get_product_discount: function () {
            var lst_price = this.get_product().lst_price;
            var unit_price = this.get_unit_price();
            var discount = 0.0;

            if ((lst_price > 0) && (lst_price !== unit_price)) {
                discount = 100*(lst_price - unit_price)/lst_price;
            }

            return discount;
        },

        get_product_discount_str: function () {
            return this.pos.chrome.format_currency_no_symbol(this.get_product_discount())
                + ' %';
        }

    });

});
