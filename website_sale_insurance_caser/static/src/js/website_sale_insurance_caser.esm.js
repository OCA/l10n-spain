import {WebsiteSale} from "@website_sale/js/website_sale";
import {patch} from "@web/core/utils/patch";

patch(WebsiteSale.prototype, {
    _updateRootProduct($form) {
        super._updateRootProduct(...arguments);
        const $checkbox = $form.find('input[name="caser_add_insurance"]');
        if ($checkbox.length) {
            this.rootProduct.caser_add_insurance = $checkbox.is(":checked") ? "1" : "";
            this.rootProduct.caser_insurance_product_page = "1";
        }
    },

    _getAdditionalRpcParams() {
        const params = super._getAdditionalRpcParams();
        // Include Caser insurance params when products have optional products
        if (this.rootProduct.caser_add_insurance) {
            params.caser_add_insurance = this.rootProduct.caser_add_insurance;
            params.caser_insurance_product_page =
                this.rootProduct.caser_insurance_product_page;
        }
        return params;
    },
});
