Este módulo añade a las cuentas bancarias el código de entidad bancaria española. Odoo
20.0 elimina los bancos (`res.bank`) y guarda los datos bancarios en cada cuenta, así que
el código se obtiene del número de cuenta cuando es un IBAN español válido.

El código se almacena, de modo que se pueden buscar, filtrar y agrupar las cuentas
bancarias por él, y otros módulos lo pueden usar, como el código de banco de las facturas
Facturae.
