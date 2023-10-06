Configurar clientes
~~~~~~~~~~~~~~~~~~~

* Accedemos a un cliente

  *  Le configuramos la opción de factura electrónica y rellenamos los datos obligatorios
  * Marcamos como método de envío FACe

* A partir de este momento, todas las facturas que validemos del cliente se enviarán automáticamente a no ser
  que marquemos la opción de `Deshabilitar envío EDI`

Envío de facturas
~~~~~~~~~~~~~~~~~
* Cuando validemos una factura de un cliente configurado a enviar por FACe se creará un registro de Envío EDI
* Mediante un job,  se generarán los datos necesarios y, posteriormente, se enviará como un registro EDI estándar
* Una vez se envíe, se alamacenará en la factura el resultado y el número de registro
* Tras eso, podremos actualizar el estado de forma online presionando el botón Actualizar Estado FACe
* Además, también podremos solicitar la anulación de la factura
  pulsando 'Cancelar Envío' e introduciendo el motivo

Es importante tener en cuenta que:

* Un registro Enviado correctamente no puede ser Eliminado
* Sólo puede existir un envío Enviado correctamente (no cancelado)
* Se genera una tarea programada que actualiza los registros enviados
  correctamente no pagados y no anulados
* En caso de que se anule la factura por parte del cliente, podremos reenviarla de nuevo

Envío manual de facturas
~~~~~~~~~~~~~~~~~~~~~~~~

* Esto podría pasarnos con facturas antiguas en las que configuramos el cliente tras emitir
  la factura o en las que hemos deshabilitado el envío automático
* Accedemos a una factura validada del cliente no enviada y pulsamos el botón
  'Spanish Facturae'. En caso de salirnos una opción de elección, deberemos seleccionara FACe
* Tras esto, funcionará de la misma forma que un envío estándar
