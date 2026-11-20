Cuando se valida una factura automáticamente envía la comunicación al servidor de la ATC.

Se debe establecer en la configuración de la compañía la agencia tributaria:
**Agencia Tributaria Canaria (1.0)**. En caso contrario, se enviará al SII de la **AEAT**.

La cabecera del envío incluye siempre ``IDVersionSii`` **1.0** (también en producción);
la ATC no admite 1.1 (error 4100).

**Art. 25 REF:** para facturas de compra con clave de régimen **17** o ventas con
clave **19**, el módulo incluye automáticamente el bloque `DatosArticulo25` en el
payload SII. Configure el tipo de bien (Lista L32) en el producto (pestaña SII)
o en la posición fiscal, y los datos del documento en la pestaña SII de la factura.
