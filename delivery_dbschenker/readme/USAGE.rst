Estas son las distintas operaciones posibles con este módulo:

Grabar servicios
~~~~~~~~~~~~~~~~

  #. Antes de confirmar el albarán, elige el transportista con la
     configuración apropriada y rellena los campos adicionales
     necesarios para el envío.
     Los campos de "Incoterms" y "Ubicación de incoterms" son
     para todos los tipos de envíos.

     - La información de entrega es:
        - Tipo de paquete (paquetes, bolsas, palés, bobinas, etc)
        - Volúmen
        - Descripción del cargo (opcional)
        - Si se pueden apilar
     - Para los envíos terrestres, necesitan:
        - Información de entrega
        - La unidad de medida entre los disponibles y su valor (si se elige Bultos se usará el campo de *Número de bultos*)
        - Marcar o no los campos checkbox
     - Para los envíos aéreos, necesitan:
        - Información de entrega
        - Aeropuerto de salida si el servicio es A2D o A2A
        - Aeropuerto destino si el servicio es D2A o A2A
        - Tipo de pre-transporte
     - Para los envíos de océano FCL, necesitan:
        - Información del contenedor (tipo de contenedor y opcionalmente su número)
        - Puerto de salida si el servicio es P2D o P2P
        - Puerto destino si el servicio es D2P o P2P
     - Para los envíos de océano LCL, necesitan:
        - Información del entrega
        - Puerto de salida si el servicio es P2D o P2P
        - Puerto destino si el servicio es D2P o P2P
        - Tipo de pre-transporte
  #. Al confirmar el albarán, el servicio se grabará en DB Schenker.
  #. Con la respuesta, se registrará en el chatter la referencia de envío y
     las etiquetas correspondientes.

Cancelar servicios
~~~~~~~~~~~~~~~~~~

  #. Al igual que en otros métodos de envío, en los albaranes de salida podemos
     cancelar un servicio determinado mediante la acción correspondiente en la
     pestaña de *Información Adicional*, sección *Información de envío* una
     vez el pedido esté confirmado y la expedición generada.
  #. Podremos generar una nueva expedición una vez cancelado si fuese necesario.

Obtener etiquetas
~~~~~~~~~~~~~~~~~~

  #. Si por error hubiésemos eliminado el adjunto de las etiquetas que obtuvimos
     en la grabación del servicio, podemos obtenerlas de nuevo pulsando en el
     botón "Etiqueta DB Schenker" que tenemos en la parte superior de la vista
     formulario del albarán.

Seguimiento de envíos
~~~~~~~~~~~~~~~~~~~~~

  #. El módulo está integrado con `delivery_state` para poder recabar la
     información de seguimiento de nuestros envíos directamente desde la API de
     DB Schenker.
  #. Para ello, vaya al albarán con un envío DB Schenker ya grabado y en la pestaña de
     *Información adicional* verá el botón *Actualizar seguimiento* para pedir
     a la API que actualice el estado de este envío en Odoo.
