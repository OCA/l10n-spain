/* Copyright 2021 Binovo IT Human Project SL
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define('l10n_es_ticketbai_pos.db', function (require) {
'use strict';

var PosDB = require("point_of_sale.DB");

PosDB.include({

    init: function(options) {
        this._super.apply(this, arguments);
        this.tbai_last_invoice_data = null;
    },

    set_tbai_json_last_invoice_data: function(data) {
        this.save('tbai_last_invoice_data', data || {});
    },

    get_tbai_json_last_invoice_data: function() {
        return this.load('tbai_last_invoice_data') || {};
    },

});
    return PosDB;
});
