Cuando se valida una factura, automáticamente genera el registro de
envío para verifactu. Cada minuto se enviarán todos aquellos registros
pendientes de enviar mediante un cron.

## Canje de facturas simplificadas (F3)

Para emitir una factura completa en sustitución de facturas
simplificadas ya registradas y declaradas, indíquelas en el campo
**Facturas simplificadas sustituidas** de la pestaña VERI\*FACTU antes de
validar. La factura se registrará como **F3** citándolas en el bloque
`FacturasSustituidas`.

Las simplificadas sustituidas no se anulan ni se rectifican, y su
importe no vuelve a declararse: el canje no es una rectificación (AEAT,
*Aclaraciones a dudas de los desarrolladores* v1.3, apartado 27). Tenga
en cuenta además que la F3 tampoco se vuelve a cobrar, ya que los tiques
sustituidos ya se cobraron en su momento.

Como toda F3 debe identificar al destinatario, no se puede validar sin
un cliente con NIF, y una simplificada sólo puede canjearse una vez.
