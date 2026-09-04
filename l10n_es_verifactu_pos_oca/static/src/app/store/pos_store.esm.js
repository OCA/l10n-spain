/*
   Copyright 2025 Alia Technologies - César Parguiñas
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

import {PosStore} from "@point_of_sale/app/store/pos_store";
import {patch} from "@web/core/utils/patch";

patch(PosStore.prototype, {
    /**
     * Gets receipt header data, including Verifactu QR code if applicable.
     * @override
     * @param order
     * @returns {*}
     */
    getReceiptHeaderData(order) {
        const result = super.getReceiptHeaderData(...arguments);
        if (order) {
            result.verifactu_qr =
                order.finalized && order._get_verifactu_qr_code_data();
        }
        return result;
    },
});
