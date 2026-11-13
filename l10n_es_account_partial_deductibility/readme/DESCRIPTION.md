En una factura de proveedor, Odoo permite indicar en cada línea el porcentaje deducible
del IVA (columna "Profesional"), por ejemplo un turismo, su combustible o sus
reparaciones con la presunción del 50 % del art. 95.Tres de la Ley del IVA. Odoo core
lleva la parte privada de la base y su IVA a la "Cuenta de acciones privadas" del diario
de compras (el plan contable español de Odoo core pone la 544) o, si no tiene, a la
cuenta por defecto del diario (la 600), y deja en la cuenta de la línea solo la parte
deducible de la base.

Según el Plan General de Contabilidad (norma de registro y valoración 12ª), el IVA
soportado no deducible forma parte del precio de adquisición del activo o del gasto.
Este módulo deja la parte privada en la cuenta de cada línea con su IVA no deducible:
una compra de 100 + 21 % de IVA deducible al 50 % carga 110,50 en la cuenta del activo o
del gasto (218, 628...), 10,50 en la 472 y abona 121 al proveedor, sin necesidad de un
diario por cada cuenta.

Los importes de la factura (base imponible, impuestos y total) y las líneas de impuestos
no cambian: solo cambia la cuenta de las líneas de la parte privada, y en una factura
con varias cuentas cada una recibe su parte privada de la base y del IVA.
