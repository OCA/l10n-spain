- Implement cancelling simplified and complete invoices from the PoS
- Configure new chaining from PoS Config
- Factura simplificada cualificada (art. 7.2 y 7.3 ROF): capturar el NIF
  del cliente en el TPV para emitir un tique deducible
  (`FacturaSimplificadaArt7273`) y evitar así el canje posterior.
- Canje de varios tiques en una única factura F3. El modelo ya lo
  admite (AEAT permite hasta 1000 facturas sustituidas y el enlace
  `pos.order.account_move` es un uno a varios), pero falta el asistente:
  `action_pos_order_invoice` factura los pedidos de uno en uno.
