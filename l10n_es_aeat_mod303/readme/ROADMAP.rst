* Los regimenes simplificado y agrícola, ganadero y forestal no están
  contemplados en el desarrollo actual.
* No se permite definir que una compañía realiza tributación conjunta.
* No se permite definir que una compañía está en concurso de acreedores.
* No se permite definir que una compañía es de una Administración Tributaria
  Foral.
* Posibilidad de marcar en el resultado el ingreso/devolución en la cuenta
  corriente tributaria.
* No se puede rellenar la casilla [109]: Devoluciones acordadas por la Agencia
  Tributaria como consecuencia de la tramitación de anteriores autoliquidaciones
  correspondientes al ejercicio y período objeto de la autoliquidación.
* El régimen de criterio de caja está contemplado por el módulo adicional
  `l10n_es_aeat_mod303_cash_basis`.
* La prorrata del IVA está contemplada por el módulo adicional
  `l10n_es_aeat_vat_prorrate`.
* Existen 2 casos de IVA no sujeto que van a la casilla 61 del modelo, que no
  están cubiertos en este módulo:

  - Con reglas de localización, pero que no corresponde a Canarias, Ceuta y
    Melilla. Por ejemplo, un abogado de España que da servicios en Francia.
  - Articulos 7,14, Otros

  Para dichos casos, se espera un módulo extra que añada los impuestos y
  posiciones fiscales.

  Más información en https://www.boe.es/diario_boe/txt.php?id=BOE-A-2014-12329
