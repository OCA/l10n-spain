* Adapta el terminal punto de venta a la legislación Española (no se permite la
  emisión de tiquets, todo deben ser facturas o facturas simplificadas con
  numeración)
* Adapta el ticket de venta a la factura simplificada, añadiendo una secuencia
  correlativa y el NIF del emisor.
* Incluye los datos del cliente (nombre, NIF y dirección) si hay uno asignado.
* Chequea que no se realice una factura simplificada con valor
  superior a 3.000 euros (la cantidad es configurable por TPV).
