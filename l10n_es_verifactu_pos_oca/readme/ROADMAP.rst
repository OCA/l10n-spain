* The amount in the ticket QR code is the order total, while the registration
  adjusts it by the taxes mapped as not included in it: the base of the exempt
  not subject ones goes down, and the quota of the withholdings -- negative --
  pushes it up. They only differ when the order carries one of those taxes;
  working it out in the PoS would mean replicating the backend tax mapping in
  the frontend.
* On a PoS that does not issue simplified invoices the ticket carries no QR
  code, while the backend does register the sale, falling back to the PoS
  reference as its serial number.
* Both the registration and the ticket QR code date the document by the UTC
  day, not by the legal day in the company's time zone, so a sale made in the
  first hours of the day is declared on the previous one.
* Implement cancelling simplified and complete invoices from the PoS
* Configure new chaining from PoS Config
* Invoicing already sent simplified invoice (PoS Order). Send anullment for the simplified and send a new one for the complete.
