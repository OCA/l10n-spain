En una cuenta bancaria, el campo **Código de entidad** aparece después del
BIC/SWIFT y se calcula a partir de un IBAN español válido. Está disponible como
columna opcional en el listado y en la búsqueda para filtrar o agrupar cuentas.

No requiere importar un catálogo ni configurar datos adicionales. Al instalar
el módulo, también se calcula para las cuentas existentes. Los IBAN vacíos,
inválidos o extranjeros dejan el campo vacío. El cálculo no modifica el nombre
del banco, el BIC ni la dirección de la cuenta.

El módulo no traslada los códigos manuales del antiguo catálogo de bancos de
Odoo 19: obtiene el código del IBAN que tenga la cuenta en Odoo 20.
