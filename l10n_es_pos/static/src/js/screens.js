/****************************************************************************
 *
 *    OpenERP, Open Source Management Solution
 *    Copyright (C) 2016 Aselcis Consulting (http://www.aselcis.com). All Rights Reserved
 *    Copyright (C) 2016 David Gómez Quilón (http://www.aselcis.com). All Rights Reserved
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Affero General Public License as
 *    published by the Free Software Foundation, either version 3 of the
 *    License, or (at your option) any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Affero General Public License for more details.
 *
 *    You should have received a copy of the GNU Affero General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 ******************************************************************************/

odoo.define('l10n_es_pos.screens', function (require) {
    "use strict";

    var core = require('web.core');
    var screens = require('point_of_sale.screens');
    var QWeb = core.qweb;
    var _t = core._t;
    var exports = {};

    screens.PaymentScreenWidget.include({
        validate_order: function (force_validate) {
            this.pos.get_order().set_simple_inv_number();
            this._super(force_validate);
        }
    });

    return exports;
});
