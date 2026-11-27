Para comprar un activo con una deducibilidad parcial del IVA (por ejemplo,
un turismo con la presunción del 50 % del art. 95.Tres de la Ley del IVA),
se indica el porcentaje en la columna "Profesional" de la línea de la
factura de proveedor. El activo que se crea desde la factura vale la base
entera más el IVA no deducible, que es su precio de adquisición (100 + 21 %
al 50 % da un activo de 110,50).

Odoo core, en cambio, lleva la parte privada de la base y su IVA a la
"Cuenta de acciones privadas" del diario de compras (el plan contable
español de Odoo core pone la 544) y deja en la cuenta del activo solo la
parte deducible de la base. Para que el saldo de la cuenta del activo
coincida con su valor, instale el módulo
`l10n_es_account_partial_deductibility`, que deja la parte privada con su
IVA en la cuenta de cada línea, tanto en los activos como en los gastos,
sin necesidad de configurar ningún diario.
