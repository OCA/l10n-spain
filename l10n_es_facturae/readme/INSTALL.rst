Este módulo depende del módulo *account_payment_partner*, *account_banking_mandate* y sus
dependencias, que se encuentran en https://github.com/OCA/bank-payment.

Para generar el archivo XML, hace falta el módulo *report_xml* que se encuentra
en https://github.com/OCA/reporting-engine.

En el caso de querer firmar el formato FacturaE desde Odoo, debe instalarse la
última versión de xmlsig mediante el comando ´pip install xmlsig´. La versión
mínima de la misma debe ser 0.1.2.
