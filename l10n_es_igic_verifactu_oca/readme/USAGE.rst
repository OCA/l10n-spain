Antes de instalar este módulo, asegúrese de tener configurada la agencia fiscal de Canarias en la configuración de la empresa.
Esto es necesario para la correcta asignación del tipo de impuesto "03" (IGIC) tanto en las facturas como en las posiciones fiscales.
Se recomienda hacer uso del modulo `account_chart_update`, esto permitira una actualizacion correcta a la localización.

Régimen minorista (clave VERI*FACTU 17): use la posición fiscal de minoristas y el IGIC teórico del producto (`igic_r_*`).
El módulo calcula la carga impositiva implícita según el art. 29.3 de la Ley 20/1991 (IGIC): ``Carga = Base × (0,7 × T) / 100``,
informando en el XML el ``TipoImpositivo`` teórico (T) y ``CargaImpositivaImplicitadeMinoristas``.

Al instalar o actualizar el módulo, las facturas en borrador de cliente (``out_invoice`` / ``out_refund``) de empresas canarias reciben las claves VERI*FACTU IGIC y las posiciones fiscales canarias sin clave quedan con el tipo ``03``.
Las facturas ya emitidas (contabilizadas) no se modifican: el histórico anterior a la adopción de VERI*FACTU queda fuera de este flujo.
