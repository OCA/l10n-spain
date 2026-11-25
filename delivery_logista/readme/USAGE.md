## Sending Shipments & Printing Labels
1. Validate the outgoing **Delivery Order** (`stock.picking`) or click **Send to Shipper**.
2. Odoo registers the expedition in Logista Parcel (`POST /shipment/v1`), queries `wsRepartoProductoPorPlazas` for the destination delegation and delivery zone, assigns 34-digit barcodes to physical packages (`stock.quant.package`), updates `delivery_state` and `carrier_tracking_ref` (`ShipmentId`), and attaches the **PDF or ZPL label** in the chatter.
3. Click **Logista Label** on the picking form at any time to reprint the shipping label, or **Print Return Label** on return pickings.
