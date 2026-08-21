When an invoice is posted, the VERI*FACTU queue is created as in
`l10n_es_verifactu_oca`. IGIC invoices use tax key `03`.

Retailer regime (key `17`): use the retailer fiscal position and the theoretical
IGIC rate on the product (`igic_r_*`). The module computes the implicit tax
load as in art. 29.3 of Ley 20/1991: `Carga = Base × (0,7 × T) / 100`.

On install or upgrade, draft customer invoices of Canary companies receive IGIC
keys. Posted invoices are left unchanged.
