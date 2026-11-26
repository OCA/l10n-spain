To configure this module:

1. Go to **Inventory > Configuration > Delivery > Shipping Methods** (or **Sales > Configuration > Shipping Methods**).
2. Open the preconfigured **Logista Parcel** shipping method (or create a new one with **Provider** = `Logista Parcel`).
3. In the **Logista Configuration** tab:
   - Enter your **Logista API Token** and **Sender Code (`Sender.Code`)** provided by Logista Parcel, and toggle **Production Environment** when ready.
   - Select your **Logista Parcel Service** (e.g. `1 - AMBIPAQ`, `4 - FRIOPAQ`), **Sector Code** (`0` Generic, `1` Pharma, `2` Food, etc.), and **Default Freight Type** (`P` Prepaid / `D` Collect).
   - Set your 2-digit **Origin Delegation Code** and 6-digit **Barcode Customer Code** for the 34-digit Code 128 label barcode, and choose your preferred **Label Format** (`PDF` or `ZPL`).
   - *(Optional)* Configure a **Default Fixed Price** or **Price Rules** by weight/volume/packages.
