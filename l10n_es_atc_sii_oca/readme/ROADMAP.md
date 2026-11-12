- Las causas de exención E1 a E6 muestran el artículo de la AEAT, aunque en los
  impuestos de IGIC tienen el significado de la ATC, que explica la ayuda del campo
  (E6 es la exención de la Zona Especial Canaria, no "Otros").
- Los impuestos de IGIC de la plantilla contable que el mapeo SII de la agencia
  tributaria canaria no incluía (comerciantes minoristas, no sujetos, exportaciones)
  reciben ahora el desglose de su tipo, mientras que antes no se comunicaban.
- Cada detalle del artículo 25 admite un solo documento, aunque la ATC acepta dos.
- No se envían todavía:
  - Las facturas F3 de sustitución de simplificadas: Odoo core no tiene ese tipo de
    factura.
  - Los cobros y pagos del criterio de caja, que van por otros servicios web, como
    en `l10n_es_aeat_sii_oca`.
