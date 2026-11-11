- Salvo el de exportación (E2) y el de venta de comerciante minorista (E1), los
  impuestos exentos de IGIC de la plantilla contable no tienen causa de exención: las
  facturas se envían con la causa del tipo de operación (E5 intracomunitaria, E2
  exportación) o sin ninguna. Hay que indicar la causa de cada impuesto exento que se
  use, teniendo en cuenta que la ATC da a los códigos otro significado que la AEAT: E6
  es la exención de la Zona Especial Canaria (art. 47 de la Ley 19/1994), no "Otros".
  Las causas E7 (art. 110 de la Ley 4/2012) y E8 (otras) de la ATC no están entre las
  de Odoo core.
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
- En las compras a comerciantes minoristas, el importe total incluye la carga
  impositiva implícita, que la ATC no suma al comprobarlo: la factura se acepta con el
  error 2045.
