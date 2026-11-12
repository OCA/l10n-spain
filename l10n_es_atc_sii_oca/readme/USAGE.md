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
impuestos de compra de IGIC o en la factura. Los impuestos de la plantilla contable ya
traen las de algunas operaciones: la exportación (02, exenta por el art. 11 de la Ley
20/1991), la venta de comerciante minorista (17, exenta por el art. 50 de la Ley
4/2012) y el recargo minorista de las importaciones (15). Las importaciones con IGIC se
comunican como DUA (F5).

Salvo el de exportación y el de venta de comerciante minorista, los impuestos exentos
de IGIC de la plantilla contable no tienen causa de exención: hay que indicar la de
cada uno que se use. La ATC da a los códigos otro significado que la AEAT (lo explica
la ayuda del campo) y tiene dos causas más, E7 (art. 110 de la Ley 4/2012) y E8
(otras), que solo pueden tener los impuestos de IGIC.

Las operaciones exentas por el artículo 25 de la Ley 19/1994 (clave 19 en ventas y 17
en compras) necesitan, en la pestaña SII de la factura, el detalle del tipo de bien y
del documento en que constan (hasta tres): sin él, la factura no se puede validar.

Las facturas del nivel avanzado del régimen especial del grupo de entidades (clave 06)
necesitan su base imponible a coste, en la pestaña SII de la factura: la ATC comprueba
que la cuota de IGIC sea la de esa base.

Los impuestos del Arbitrio sobre Importaciones y Entregas de Mercancías (AIEM), que la
plantilla contable no trae, se marcan con la casilla AIEM: su cuota se envía aparte
del desglose de IGIC.

En las certificaciones de obra para administraciones públicas (clave 14), la ATC
exige la fecha de operación, posterior a la de la factura: es la fecha de entrega de
la factura.
