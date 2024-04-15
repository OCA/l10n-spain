- Es necesario ir a los modos de pago e indicar su correspondencia con
  los códigos de Facturae.
- La dirección del contacto establecido en la factura, a la cual se va
  a remitir la factura de venta que queremos exportar, debe estar marcada
  como facturae y debe tener cubiertos los datos de Oficina contable,
  Órgano gestor y Unidad tramitadora.
- Si deseamos permitir la firma del xml generado desde Odoo mediante la
  opción que ofrece el wizard de exportación, tenemos que irnos a
  Invoicing -> Configuration -> Certificates AEAT. Crearemos un nuevo
  certificado donde cargaremos el fichero .pfx que hayamos obtenido,
  estableceremos un nombre para el certificado y la carpeta donde se ubicará.
  Una vez creado pulsaremos el botón **Obtain Keys**  y nos pedirá que
  introduzcamos la contraseña del certificado. Una vez obtenidas las claves
  activaremos el certificado pulsando sobre el botón "To Active".
