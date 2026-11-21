- La declaración sólo se puede realizar para personas jurídicas.
- No se calculan operaciones intragrupo.
- No se contempla el régimen de criterio de caja.
- No se contempla el régimen especial de bienes usados, objetos de arte,
  antigüedades y objetos de colección.
- No se contempla el régimen especial de agencias de viaje.
- No se contempla el recargo de equivalencia de impuesto al tabaco
  (casillas 41 y 42).
- El régimen especial de la agricultura, ganadería y pesca sólo se contempla
  en parte: se calculan las compensaciones satisfechas a quienes están acogidos
  a él (casillas 60 y 61), pero no las operaciones del propio régimen
  (casilla 101).
- No se contempla la prorrata general de IVA: las cuotas deducibles no descuentan
  las líneas de prorrata, porque `l10n_es_aeat_mod390_vat_prorate` no se ha
  migrado desde la 18.0.
- No se declaran las operaciones de la ventanilla única (OSS), porque
  `l10n_es_aeat_mod390_oss` no se ha migrado desde la 18.0.
- No se contempla el régimen simplificado.
- No se contempla el régimen de deducción diferenciado.
- No se tienen en cuenta tributaciones territoriales.
- Las transferencias de bienes en consigna a otro Estado miembro (impuesto
  `s_iva0_bc`) no suman en ninguna casilla: hasta que el cliente retira los
  bienes no hay entrega (art. 9 bis de la Ley del IVA) y solo se declaran en el
  349. La entrega exenta posterior se factura con el impuesto de entregas
  intracomunitarias, que va a la casilla 103.
