Cuando se valida una factura automáticamente envía la comunicación al servidor de la ATC.

Se debe establecer en la configuración de la compañía la agencia tributaria:
**Agencia Tributaria Canaria (1.0)**. En caso contrario, se enviará al SII de la **AEAT**.

La cabecera del envío incluye ``IDVersionSii``: **1.1** en producción y **1.0** si la
compañía tiene activado el **modo de prueba SII** (requisito del entorno de cautela ATC).
