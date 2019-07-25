* Accedemos a un cliente y le configuramos la factura electrónica
* Accedemos a una factura validada del cliente y pulsamos el botón
  'Enviar a FACe'
* Podremos añadir adjuntos que al envío de la factura original
* Pulsamos 'Enviar' en el registro de envío a FACe
* Si el envío es correcto, nos mostrará el resultado y el número de registro
* Si el envío es correcto, podremos actualizar el estado de forma online
* Si el envío es correcto, podremos solicitar la anulación de la factura
  pulsando 'Cancelar Envío' e introduciendo el motivo
* Un registro Enviado correctamente no puede ser Eliminado
* Sólo puede existir un envío Enviado correctamente
* Se genera una tarea programada que actualiza los registros enviados
  correctamente no pagados y no anulados
