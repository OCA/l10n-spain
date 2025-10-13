/** @odoo-module **/

import {ErrorPopup} from "@point_of_sale/app/errors/popups/error_popup";
import {InvoiceButton} from "@point_of_sale/app/screens/ticket_screen/invoice_button/invoice_button";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";

patch(InvoiceButton.prototype, {
    setup() {
        super.setup(...arguments);
        this.popup = useService("popup");
    },

    get commandName() {
        let cName = super.commandName;
        const order = this.props.order;
        if (order) {
            cName = this.isAlreadyInvoiced
                ? _t("Reprint Invoice")
                : order.siiSessionClosed
                ? _t("Cannot Invoice")
                : _t("Invoice");
        }
        return cName;
    },

    async _invoiceOrder() {
        const order = this.props.order;
        if (!order) {
            return;
        }

        if (order.siiSessionClosed) {
            this.popup.add(ErrorPopup, {
                title: _t("Session is closed"),
                body: _t("Cannot invoice order from closed session."),
            });
            return;
        }

        return await super._invoiceOrder(...arguments);
    },
});
