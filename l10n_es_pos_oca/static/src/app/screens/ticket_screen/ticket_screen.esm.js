/** @odoo-module */

/* Copyright 2016 David Gómez Quilón <david.gomez@aselcis.com>
   Copyright 2018-19 Tecnativa - David Vidal
   Copyright 2024 (APSL-Nagarro) - Antoni Marroig
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

import {TicketScreen} from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";

patch(TicketScreen.prototype, {
    _getSearchFields() {
        const fields = super._getSearchFields();
        fields.SIMPLIFIED_INVOICE = {
            repr: (order) => order.name,
            displayName: _t("Simplified Invoice"),
            modelField: "l10n_es_unique_id",
        };
        return fields;
    },
});
