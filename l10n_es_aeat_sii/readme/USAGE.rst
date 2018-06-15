Cuando se valida una factura automáticamente envia la comunicación al servidor
de AEAT.

Sistema de comprobación y contraste
***********************************

* Cada factura tiene un boton 'Contrastar con AEAT' al pulsarlo crea un Job y al finalizar se muestra en los campos "Estado cuadre" y "Estado contraste AEAT" el resultado global.
* "Estado cuadre": son los estados que proporciona la AEAT para saber si la contraparte ha enviado los mismo datos.
* "Estado contraste AEAT": comprueba si los datos en el servidor de la AEAT son los mismos que en Odoo, puede ocurrir que algún empleado o asesor externo entre en el sitio web de la AEAT y realice cambios sin pasar por Odoo.
* Desde el menú Declaraciones AEAT también existe la opción de realizar una comprobación por meses de todas las facturas, en este caso se muestra el resumen de datos globales y el detalle de aquellas facturas que no han podido contrastarse por alguno de los problemas arriba indicados.
