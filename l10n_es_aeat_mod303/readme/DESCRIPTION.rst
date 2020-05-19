Módulo para la presentación del modelo 303 (IVA - Autodeclaración) de la
Agencia Española de Administración Tributaria.

Instrucciones del modelo: http://goo.gl/pgVbXH

Diseño de registros BOE en Excel: https://goo.gl/HKOGec

Incluye la exportación al formato BOE para su uso telemático y la creación
del asiento de regularización de las cuentas de impuestos.

Para el régimen de criterio de caja, hay que buscar el módulo
*l10n_es_aeat_mod303_cash_basis*.

* La prorrata del IVA está contemplada por el módulo adicional `l10n_es_aeat_vat_prorrate`.

* Existen 2 casos de IVA no sujeto que van a la casilla 61 del modelo, que no
  están cubiertos en este módulo:

  - Con reglas de localización, pero que no corresponde a Canarias, Ceuta y
    Melilla. Por ejemplo, un abogado de España que da servicios en Francia.
  - Articulos 7,14, Otros

  Para dichos casos, se espera un módulo extra que añada los impuestos y
  posiciones fiscales.

  Más información en https://www.boe.es/diario_boe/txt.php?id=BOE-A-2014-12329
