import {AlertDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {InvoiceButton} from "@point_of_sale/app/screens/ticket_screen/invoice_button/invoice_button";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";

patch(InvoiceButton.prototype, {
    get commandName() {
        let cName = super.commandName;
        const order = this.props.order;
        if (order) {
            cName = this.isAlreadyInvoiced
                ? _t("Reprint Invoice")
                : order.sii_session_closed
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

        if (order.sii_session_closed) {
            this.env.services.dialog.add(AlertDialog, {
                title: _t("Session is closed"),
                body: _t("Cannot invoice order from closed session."),
            });
            return;
        }

        return await super._invoiceOrder(...arguments);
    },
});
