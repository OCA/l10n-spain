1. To make DeCA available for incoming transfers, go to **Inventory > Configuration > Operation Types**, open an incoming operation type, and enable **Enable DeCA**. This option is shown only for incoming operation types.
2. Ensure Inventory users (`stock.group_stock_user`) can work with the relevant transfers. The DeCA controls and report are restricted to this group.
3. Review the effective Odoo weight unit and product weights in your environment. The module does not validate those source values.
4. If the effective weight unit or a product's logistics unit changes later, stored DeCA weights are not recalculated automatically. Assess and selectively recompute affected `deca_weight` values.

The module computes DeCA weights during installation for existing stock moves and pickings. It uses the done quantity when non-zero, otherwise the planned quantity, excludes cancelled moves, and stores the result in kilograms without rounding before display (up to Odoo's native precision, six decimal places). Invalid effective weight units, or positive weights too small to display at six decimals, prevent DeCA issuance but do not block stock operations.

## Security and sharing

The **Share DeCA** link and QR code contain a bearer token. Anyone with the link can download the PDF while the source transfer exists. Use the button-provided link only through authorized channels. Copied transfers and backorders receive a new token.

For a QR code to work outside the internal network, deploy Odoo over HTTPS and configure an accessible `web.base.url` for the scanning devices. Invalid, missing, or unrelated tokens return a generic not-found response; the controller does not serve an older PDF as the current one.

## Storage and deletion

Issued PDFs cannot be edited or directly deleted while their source transfer exists. Deleting the source transfer also removes its DeCA PDFs, so this is not a retention guarantee. The module does not define retention periods or write-once storage, and does not provide a legal-retention or legal-compliance guarantee.

Generic operations that directly write the protected issued attachment may fail. In particular, use **Share DeCA** rather than generating a separate public token for the attachment itself. Attachment-storage migrations should be assessed before execution.
