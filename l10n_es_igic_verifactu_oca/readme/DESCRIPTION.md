Glue module to send Canary Islands IGIC invoices through AEAT VERI*FACTU.

It maps native `es_canary_*` taxes and fiscal positions (clave impuesto `03`)
onto `l10n_es_verifactu_oca`. The SOAP endpoint is AEAT, not ATC.

Before installing, set the Canary tax agency on the company so draft invoices
and fiscal positions get tax key `03`.
