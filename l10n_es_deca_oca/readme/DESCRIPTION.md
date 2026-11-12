This module generates a DeCA (electronic Control of Administration) PDF for land carriage of goods from eligible Inventory transfers (`stock.picking`). The report refers to Spanish Law 15/2009 on the contract for the carriage of goods.

This Odoo 18 backport is based on the implementation proposed in [OCA/l10n-spain#5281](https://github.com/OCA/l10n-spain/pull/5281) and the upstream source commit `c10d5970feeffe1baf7cee6a2b0f6566698da7ed`.

The upstream proposal has not been merged. Its provenance does not constitute OCA endorsement, maintenance, approval, or a legal-compliance guarantee for this backport.

Scope:

* Outgoing transfers are eligible by default.
* Incoming transfers are eligible only when **Enable DeCA** is enabled on their operation type.
* Internal transfers are not eligible.
* Batch-transfer (`stock_picking_batch`) and purchase-order triggers are not provided.
