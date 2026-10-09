Módulo para la presentación inmediata de la facturación desde TPV.

Los tiques se registran como facturas simplificadas (F2). Si más tarde
el cliente pide factura completa, al pulsar **Factura** sobre el pedido
se emite una factura de canje en sustitución del tique, que se registra
como **F3** citándolo en el bloque `FacturasSustituidas`. El tique ni se
anula ni se rectifica, y su importe no vuelve a declararse: la
sustitución no es una rectificación (AEAT, *Aclaraciones a dudas de los
desarrolladores* v1.3, apartado 27, y art. 15.6 §2 del RD 1619/2012).

Como toda F3 debe identificar al destinatario, el canje se rechaza si el
pedido no tiene un cliente con NIF.
