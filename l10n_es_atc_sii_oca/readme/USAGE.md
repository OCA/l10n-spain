Cuando se valida una factura, se envía automáticamente al SII de la Agencia Tributaria
Canaria (ATC).

Se debe establecer la agencia tributaria **Agencia Tributaria Canaria** en la compañía
o, en una compañía peninsular con un establecimiento en Canarias, en los diarios de las
facturas de ese establecimiento. En caso contrario, las facturas se envían al SII de la
**AEAT**.

Los impuestos de IGIC forman parte del plan contable español general. Odoo los archiva
en las compañías cuya provincia no es canaria: en ese caso hay que activar los que se
usen.

A la ATC solo se comunican los impuestos de IGIC (aplicabilidad IGIC) y las retenciones,
y a la AEAT solo los de IVA. El desglose sale de los datos españoles de cada impuesto
(tipo, alcance y bien de inversión), como en `l10n_es_aeat_sii_oca`.

Las claves de registro de las compras con IGIC (15, 16 y 17) se pueden indicar en los
impuestos de compra de IGIC o en la factura.
