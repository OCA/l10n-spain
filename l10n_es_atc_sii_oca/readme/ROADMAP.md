- Las causas de exención E1 a E6 muestran el artículo de la AEAT, aunque en los
  impuestos de IGIC tienen el significado de la ATC, que explica la ayuda del campo
  (E6 es la exención de la Zona Especial Canaria, no "Otros").
- Los impuestos de IGIC de la plantilla contable que el mapeo SII de la agencia
  tributaria canaria no incluía (comerciantes minoristas, no sujetos, exportaciones)
  reciben ahora el desglose de su tipo, mientras que antes no se comunicaban.
- No se envían todavía los datos que la ATC pide en algunas claves u operaciones: el
  bloque `DatosArticulo25` de las claves 17 de compras y 19 de ventas (errores 2028 y
  2031, sin él la ATC rechaza la factura), la `FechaOperacion` de las certificaciones
  de obra para administraciones públicas (clave 14), la `BaseImponibleACoste` del
  régimen de grupos de entidades (clave 06), la cuota del AIEM (`CuotaAIEM`), las
  facturas F3 de sustitución de simplificadas y los cobros y pagos del criterio de
  caja.
