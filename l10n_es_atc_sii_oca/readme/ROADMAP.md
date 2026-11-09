- El `aeat.sii.map` que este módulo incluye para la agencia tributaria canaria nunca es
  el que se usa. `_get_aeat_taxes_map` de `l10n_es_aeat_sii_oca` busca
  `tax_agency_id in (agency, False)` con `limit=1` y sin orden, así que el mapeo
  genérico que crea `l10n_es_aeat_sii_oca` gana por orden de identificador y los
  impuestos de IGIC nunca se clasifican: una factura con solo impuestos de IGIC llega a
  la ATC con el desglose vacío. O la búsqueda prefiere el mapeo de la agencia frente al
  genérico, o este módulo tiene que sobrescribirla.
