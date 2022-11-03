* No se comprueba el límite en operaciones separadas para un mismo cliente, algo
  que Hacienda proscribe.
* El soporte para usuarios concurrentes sobre una misma sesión es limitado y solo es
  fiable si ambos puestos están online. En el caso de que cualquiera de ellos estuviese
  offline, se correría el riesgo de solapar la secuencia de factura simplificada. Se
  recomienda que en estos casos se añada mejor una configuración de punto de venta
  adicional.
