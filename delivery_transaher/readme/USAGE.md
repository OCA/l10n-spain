## Calculating Shipping Rates on Sales Orders
1. Create or open a **Sales Order** and click **Add shipping**.
2. Select **Transaher Smart Logistic** and click **Get rate**.
3. The wizard computes gross and volumetric weight (using OCA `stock_picking_volume`) and displays the **Internal Transaher Cost (€)**, **Chargeable Weight (kg)**, and a detailed **Transaher Tariff Breakdown**.
4. Click **Add** to apply the shipping line and store the internal estimated cost on the order.

## Sending Shipments & Printing Labels from Pickings
1. Set **Number of Packages** (`number_of_packages` from `delivery_package_number`) or pack lines into physical packages; `volume` is computed automatically by `stock_picking_volume`.
2. Validate the outgoing **Delivery Order** (`stock.picking`) or click **Send to Shipper**.
3. Odoo registers the expedition in Transaher via `awsprcsatsoap`, sets `delivery_state` (`shipping_recorded_in_carrier`) and `date_shipped` (`delivery_state`), stores the composite reference (`Holding.Seccion.Centro.CodExpedicion`) and destination routing info, assigns 24-digit Transaher barcodes to packages, and attaches the shipping label in the chatter.
4. In the **Additional Info** and **Transaher Logistics** tabs of the picking, you can:
   - Configure freight terms (`Portes`), postal repetition code, observations (`Observaciones 1 & 2`), insured value, or COD (`Contra reembolso`) prior to sending.
   - Click **Transaher Label (WS)** to reprint official labels via `wsEtiExpSOAP` or **Print Standard Barcode Label (QWeb)** to print the local 100x150mm 24-digit barcode label.
   - Click **Update tracking state** (`tracking_state_update` from `delivery_state`) or **Update Tracking & Invoiced Costs** to fetch live statuses, events, incidences, package SSCCs, and invoiced freight costs via `wsInformacionTransporte` (also updated automatically by `delivery_state`'s scheduled action).

## Generating the Daily Loading Manifest
1. Open the Transaher shipping method and click the **Daily Manifest** smart button (or navigate to **Inventory > Reporting > Transaher Daily Manifest**).
2. Select the **Date From** and **Date To** range and click **Query & Generate PDF Manifest** or **Print PDF Directly**.
