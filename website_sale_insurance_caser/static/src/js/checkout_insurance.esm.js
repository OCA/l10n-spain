import publicWidget from "@web/legacy/js/public/public_widget";
import {rpc} from "@web/core/network/rpc";

publicWidget.registry.caserInsuranceCheckout = publicWidget.Widget.extend({
    selector: ".oe_website_sale",
    events: {
        "click a[name='website_sale_main_button']": "_onCheckoutClick",
        "click #addInsuranceBtn": "_onAddInsurance",
        "click #skipInsuranceBtn": "_onSkipInsurance",
        "click #closeInsuranceModal": "_onSkipInsurance",
        "click #toggleAllInsurance": "_onToggleAll",
    },

    start() {
        this._checkoutHref = this.el
            .querySelector("a[name='website_sale_main_button']")
            ?.getAttribute("href");
        return this._super(...arguments);
    },

    async _onCheckoutClick(ev) {
        if (!window.location.pathname.includes("/shop/cart")) {
            return;
        }
        ev.preventDefault();
        const data = await rpc("/shop/caser_insurance/get_uninsured_products");
        if (data.products?.length) {
            this._showInsuranceModal(data.products);
        } else {
            window.location.href = this._checkoutHref;
        }
    },

    _showInsuranceModal(products) {
        const $list = this.$("#uninsured_products_list");
        $list.empty();
        const totalUnits = products.reduce((sum, p) => sum + p.quantity, 0);
        const hasMultiUnit = totalUnits > 1;

        products.forEach((product) => {
            const checked = hasMultiUnit ? "" : "checked";
            for (let i = 0; i < product.quantity; i++) {
                $list.append(`
                    <div class="d-flex align-items-center gap-3 py-2 border-bottom">
                        <input class="form-check-input flex-shrink-0 insurance-checkbox"
                               type="checkbox" ${checked}
                               data-line-id="${product.line_id}"
                               id="ins_${product.line_id}_${i}"/>
                        <img src="${product.image_url}" alt="${product.product_name}"
                             class="o_image_64_max img rounded"/>
                        <label class="form-check-label flex-grow-1 mb-0" for="ins_${product.line_id}_${i}">
                            ${product.product_name}
                            <small class="text-muted ms-2">+€${product.insurance_price.toFixed(2)}</small>
                        </label>
                    </div>
                `);
            }
        });

        const $toggle = this.$("#toggleAllInsurance");
        if (hasMultiUnit) {
            $toggle.removeClass("d-none");
        } else {
            $toggle.addClass("d-none");
        }

        this.$("#caserInsuranceModal").modal("show");
    },

    _onToggleAll() {
        const $checkboxes = this.$(".insurance-checkbox");
        const allChecked = $checkboxes.length === $checkboxes.filter(":checked").length;
        $checkboxes.prop("checked", !allChecked);
    },

    _onSkipInsurance() {
        this.$("#caserInsuranceModal").modal("hide");
        window.location.href = this._checkoutHref;
    },

    async _onAddInsurance(ev) {
        ev.preventDefault();
        const lineInsurances = {};
        this.$(".insurance-checkbox:checked").each(function () {
            const lineId = $(this).data("line-id");
            lineInsurances[lineId] = (lineInsurances[lineId] || 0) + 1;
        });

        await rpc("/shop/caser_insurance/update_insurance", {
            line_insurances: lineInsurances,
        });
        window.location.reload();
    },
});

export default publicWidget.registry.caserInsuranceCheckout;
