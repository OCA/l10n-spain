* No se comprueba el límite en operaciones separadas para un mismo cliente, algo
  que Hacienda proscribe.
* El modo de gestión de inventario en tiempo real, si se pierde la conexión a internet,
  las ventas se quedan pendientes de enviar a la base de datos hasta que la conexión
  vuelve. En ese estado no se asigna número de factura simplificada, aunque cuando la
  conexión ha regresado, la numeración de la factura simplicada es correcta.
