Lo primero que necesitarás serán una credenciales para el API Atlas. Contacta con tu oficina de SEUR
para conseguirlas y pruébalas en [el sitio principal del API Atlas](https://sds.seur.io).

Una vez que tu oficina te facilite las credenciales necesarias, ya puedes configurar
tus transportistas.

De momento, no hay implementados métodos de cálculo de tarifas de envío, de modo que
necesitarás apoyarte en los métodos de precio de Odoo seleccionándolos en el campo *Método de precio*.

Para configurar tus servicios SEUR, debes ir a:

1. *Inventario/Ventas > Configuración > Métodos de envío* y editar o crear uno nuevo.
2. Escoge *Seur Atlas* como proveedor.
3. Configura tus credenciales de Atlas: NIF, código de cuenta, nombre de usuario, secreto, y código de cliente.
4. Configura el servicio y producto SEUR que necesites.
5. Configura el formato de etiqueta que necesites:
   - ZPL
   - PDF
   - A4 troquelado
6. Configura la plantilla de etiqueta y el tipo de salida.

Si deseas configurar varios servicios con las mismas credenciales, duplica un ya creado
y cambia el servicio o el producto en la copia.

El `timeout` por defecto para las peticiones a la API es de 5 segundos. Se puede
configurar uno distinto con la clave `seur_atlas_timeout` en `ir.config_parameter`.
