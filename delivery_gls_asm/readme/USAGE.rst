Estas son las distintas operaciones posibles con este módulo:

Grabar servicios
~~~~~~~~~~~~~~~~

  #. Al confirmar el albarán, el servicio se grabará en GLS.
  #. Con la respuesta, se registrará en el chatter la referencia de envío y
     las etiquetas correspondientes.
  #. Para gestionar los bultos del envío, se puede utilizar el campo de número
     de bultos que añade `delivery_package_number` (ver el README para mayor
     información) o bien el flujo nativo de Odoo con paquetes de envío. El
     módulo mandará a la API de GLS/ASM el número correspondiente y podremos
     descargar las etiquetas en PDF con su correspondiente numeración.

Cancelar servicios
~~~~~~~~~~~~~~~~~~

  #. Al igual que en otros métodos de envío, en los albaranes de salida podemos
     cancelar un servicio determinado mediante la acción correspondiente en la
     pestaña de *Información Adicional*, sección *Información de entrega* una
     vez el pedido esté confirmado y la expedición generada.
  #. Podremos generar una nueva expedición una vez cancelado si fuese necesario.

Obtener etiquetas
~~~~~~~~~~~~~~~~~~

  #. Si por error hubiésemos eliminado el adjunto de las etiquetas que obtuvimos
     en la grabación del servicio, podemos obtenerlas de nuevo pulsando en el
     botón "Etiqueta GLS" que tenemos en la parte superior de la vista
     formulario del albarán.

Seguimiento de envíos
~~~~~~~~~~~~~~~~~~~~~

  #. El módulo está integrado con `delivery_state` para poder recabar la
     información de seguimiento de nuestros envíos directamente desde la API de
     GLS-ASM.
  #. Para ello, vaya al albarán con un envío GLS ya grabado y en la pestaña de
     *Información adicional* verá el botón *Actualizar seguimiento* para pedir
     a la API de GLS que actualice el estado de este envío en Odoo.

Manifiesto de envíos
~~~~~~~~~~~~~~~~~~~~

  #. Para obtener el manifiesto de expediciones que firmaría el repartidor,
     puede ir al menú *Inventario > Informes > Manifiesto de Envíos GLS*.
  #. También puede obtener el manifiesto desde un smart button en el formulario
     del transportista.
  #. En el asistente, seleccione el servicio GLS del cual quiere sacar el
     manifiesto y la fecha desde la que desea listar los envíos.
  #. Pulse en el botón "Manifiesto GlS" para obtener un listado en PDF de los
     envíos del servicio seleccionado.

Depuración de errores
~~~~~~~~~~~~~~~~~~~~~

  #. En cada servicio GLS-ASM dispone de una pestaña llamada "Técnico" en la
     que puede consultar la última petición y respuesta a la API de GLS-ASM.
     Esto le servirá como ayuda a la hora de depurar posibles errores de
     comunicación.
  #. También puede activar Odoo con `--log-level=debug` para refistrar las
     peticiones y las respuestas en el log.
