- Las causas de exención E1 a E6 muestran el artículo de la AEAT, aunque en los
  impuestos de IGIC tienen el significado de la ATC, que explica la ayuda del campo
  (E6 es la exención de la Zona Especial Canaria, no "Otros").
- Los impuestos de IGIC de la plantilla contable que el mapeo SII de la agencia
  tributaria canaria no incluía (comerciantes minoristas, no sujetos, exportaciones)
  reciben ahora el desglose de su tipo, mientras que antes no se comunicaban. En
  una base migrada desde 18.0 también los ya usados en facturas: la migración les
  da los datos de IGIC y deja en el registro los que cambia. Las facturas ya
  enviadas no se reenvían.
- Odoo core define el impuesto `igic_sop_5_inv` (IGIC 5 % bienes de inversión) con
  un 3 %: las compras con él van a la ATC con `TipoImpositivo` 3 y la cuota del 3 %.
  Este módulo no lo corrige; hay que revisar el porcentaje del impuesto en la
  compañía hasta que se arregle en Odoo core.
- Cada detalle del artículo 25 admite un solo documento, aunque la ATC acepta dos.
- No se envían todavía:
  - Las facturas F3 de sustitución de simplificadas: Odoo core no tiene ese tipo de
    factura.
  - Los cobros y pagos del criterio de caja, que van por otros servicios web, como
    en `l10n_es_aeat_sii_oca`.
