/*
   Copyright 2025 Alia Technologies - César Parguiñas
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

import {ConnectionLostError} from "@web/core/network/rpc";
import {PosStore} from "@point_of_sale/app/store/pos_store";
import {patch} from "@web/core/utils/patch";

patch(PosStore.prototype, {
    getReceiptHeaderData(order) {
        const result = super.getReceiptHeaderData(...arguments);
        if (order) {
            //TODO
            // result.verifactu_qr = order.finalized && order._get_verifactu_qr_code_data();
            result.verifactu_qr = order._get_verifactu_qr_code_data();
        }
        console.log('RECEIPT HEADER DATA PATCH', result);
        return result;
    },
});
