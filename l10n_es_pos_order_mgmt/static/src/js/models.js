/* Copyright 2018 Tecnativa - David Vidal
   License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */

odoo.define('l10n_es_pos_order_mgmt.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');

    var order_super = models.Order.prototype;
    models.Order = models.Order.extend({

        init_from_JSON: function (json) {
            order_super.init_from_JSON.apply(this, arguments);
            this.origin_simplified_invoice = json.origin_simplified_invoice;
        },
        export_as_JSON: function () {
            var res = order_super.export_as_JSON.apply(this, arguments);
            if (this.origin_simplified_invoice) {
                res.origin_simplified_invoice = this.origin_simplified_invoice;
            }
            return res;
        },
    });
});
