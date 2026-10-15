- The amount in the ticket QR code is the order total, while the
  registration adjusts it by the taxes mapped as not included in it: the
  base of the exempt not subject ones goes down, and the quota of the
  withholdings -- negative -- pushes it up. They only differ when the
  order carries one of those taxes; working it out in the PoS would mean
  replicating the backend tax mapping in the frontend.
- Both the registration and the ticket QR code date the document by the
  UTC day, not by the legal day in the company's time zone, so a sale
  made in the first hours of the day is declared on the previous one.
- Implement cancelling simplified and complete invoices from the PoS
- Configure new chaining from PoS Config
- Factura simplificada cualificada (art. 7.2 y 7.3 ROF): capturar el NIF
  del cliente en el TPV para emitir un tique deducible
  (`FacturaSimplificadaArt7273`) y evitar así el canje posterior.
- Canje de varios tiques en una única factura F3. El modelo ya lo
  admite (AEAT permite hasta 1000 facturas sustituidas y el enlace
  `pos.order.account_move` es un uno a varios), pero falta el asistente:
  `action_pos_order_invoice` factura los pedidos de uno en uno.
