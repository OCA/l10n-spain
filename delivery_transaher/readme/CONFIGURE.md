To configure this module:

1. Go to **Inventory > Configuration > Delivery > Shipping Methods** (or **Sales > Configuration > Shipping Methods**).
2. Open the preconfigured **Transaher Smart Logistic** shipping method or create a new one with **Provider** = `Transaher`.
3. In the **Transaher Web Service Configuration** tab:
   - Enter your **Test Client Code (`CodigoCliente`)**, **Test Password (`PasswordCliente`)**, **Production Client Code (`CodigoCliente`)**, and **Production Password (`PasswordCliente`)** provided by Grupo Transaher.
   - Verify the **Holding Code** (`0`), **Section Code** (`10`), **Origin Center Code** (e.g. `461` for Valencia or `81` for Barcelona), **Protocol Code** (`20`), and **Default Freight Terms (`Tipo de Portes`)** (`1` Freight Prepaid / `2` Freight Collect).
   - Select your **Label Generation Mode** (`Transaher Web Service PDF (with Local QWeb Label Fallback)`, `Transaher Web Service Only (wsEtiExpSOAP)`, or `Local Standard Transaher Label PDF (24-digit Barcode)`), **wsEtiExpSOAP Package Tag (`<Bultos>`)**, and **Initial Print Position (Multi-Label Sheet)**.
   - Click the **Test Token wsgetToken** smart button to validate authentication against `wsgetToken.svc`.
4. In the **Transaher Tariffs & Costs** tab:
   - Configure **Volumetric Factor (kg / m³)** (e.g. `250`), fuel, COD, and insurance surcharges, **Free Shipping for Customer (Keep Internal Cost)**, and local zone/province/ZIP/weight/package tariff rules.

