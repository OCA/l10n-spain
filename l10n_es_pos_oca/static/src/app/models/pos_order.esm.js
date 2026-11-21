/* Copyright 2016 David Gómez...
   Copyright 2025 Alia Technologies - César Parguiñas
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

import {PosOrder} from "@point_of_sale/app/models/pos_order";
import {patch} from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    get_l10n_es_unique_id() {
        return this.l10n_es_unique_id ? this.l10n_es_unique_id : "";
    },
});
