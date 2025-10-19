* Factura de cliente

  * Se genera el fichero y se firma al validar la factura.
* Factura de cliente rectificativa

  * Diferencias (total o parcial)

    * Parcial: se genera el fichero y se firma al validar la factura rectificativa. La factura se ha tenido que generar desde el asistente de emitir rectificativa
    * Total: se genera el fichero y se firma al crear la rectificativa desde el asistente de emitir rectificativa, escogiendo la opción `cancelar`

* Anulación de factura

  * Se genera un nuevo fichero de anulación y se firma al cancelar una factura validada. La factura se queda en estado cancelado y no puede ser pasada a borrador para volver a validarse.

* Secuencias de diarios (aplicado cuando la compañía habilita TicketBAI)

  * Por limitaciones de TicketBAI, se eliminan los sufijos de las secuencias de los diarios de ventas.
  * Por legalidad, se obliga a especificar una secuencia dedicada para las facturas rectificativas.
