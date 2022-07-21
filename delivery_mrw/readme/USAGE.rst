Estas son las distintas operaciones posibles con este módulo:

Crear envío
~~~~~~~~~~~~~~~~

  #. Al confirmar el albarán, el envío se creará en MRW.
  #. Con la respuesta, se registrará en el chatter la referencia de envío y
     las etiquetas correspondientes.
  #. Para gestionar los bultos del envío, se puede utilizar el campo de número
     de bultos que añade `delivery_package_number` (ver el README para mayor
     información) o bien el flujo nativo de Odoo con paquetes de envío. El
     módulo mandará a la API de MRW el número correspondiente y podremos
     descargar las etiquetas en PDF con su correspondiente numeración.

Cancelar envíos
~~~~~~~~~~~~~~~~~~

  #. Al igual que en otros métodos de envío, en los albaranes de salida podemos
     cancelar un envío determinado mediante la acción correspondiente en la
     pestaña de *Información Adicional*, sección *Información de entrega* una
     vez el pedido esté confirmado y la expedición generada.
  #. Podremos generar una nueva expedición una vez cancelado si fuese necesario.

Obtener etiquetas
~~~~~~~~~~~~~~~~~~

  #. Si por error hubiésemos eliminado el adjunto de las etiquetas que obtuvimos
     en la grabación del servicio, podemos obtenerlas de nuevo pulsando en el
     botón "Etiqueta MRW" que tenemos en la parte superior de la vista
     formulario del albarán.

Seguimiento de envíos
~~~~~~~~~~~~~~~~~~~~~

  #. El módulo incorpora el botón 'Seguimiento' en el albarán que redirige a la página
     de MRW del envío en cuestión. También se puede usar el botón "Actualizar estado de
     Pedido" para cargar directamente en odoo el estado del pedido usando la API de MRW.


Manifiesto de envíos
~~~~~~~~~~~~~~~~~~~~

  #. Para obtener el manifiesto de expediciones que firmaría el repartidor,
     puede ir al menú *Inventario > Informes > Manifiesto de Envíos MRW*.
  #. También puede obtener el manifiesto desde un smart button en el formulario
     del transportista.
  #. En el asistente, seleccione el servicio MRW del cual quiere sacar el
     manifiesto (si se deja vacío cogerá todos) y la fecha en la cual desea listar los envíos.
  #. Pulse en el botón "Descargar Manifiesto" para obtener un listado en PDF de los
     envíos del servicio seleccionado.


Depuración de errores
~~~~~~~~~~~~~~~~~~~~~

  #. Es importante tener en cuenta que solo funcionará para envíos desde España.
