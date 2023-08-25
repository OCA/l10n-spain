odoo.define("l10n_es_pos_sii.InvoiceButton", function (require) {
    "use strict";

    const InvoiceButton = require("point_of_sale.InvoiceButton");
    const Registries = require("point_of_sale.Registries");

    // eslint-disable-next-line no-shadow
    const OverloadInvoiceButton = (InvoiceButton) =>
        // eslint-disable-next-line no-shadow
        class OverloadInvoiceButton extends InvoiceButton {
            get commandName() {
                let cName = super.commandName;
                if (this.props.order) {
                    cName = this.isAlreadyInvoiced
                        ? this.env._t("Reprint Invoice")
                        : this.props.order.siiSessionClosed
                        ? this.env._t("Cannot Invoice")
                        : this.env._t("Invoice");
                }
                return cName;
            }
            async _invoiceOrder() {
                const order = this.props.order;
                if (!order) return;

                if (order.siiSessionClosed) {
                    this.showPopup("ErrorPopup", {
                        title: this.env._t("Session is closed"),
                        body: this.env._t("Cannot invoice order from closed session."),
                    });
                    return;
                }

                return super._invoiceOrder(...arguments);
            }
        };

    Registries.Component.extend(InvoiceButton, OverloadInvoiceButton);
});
