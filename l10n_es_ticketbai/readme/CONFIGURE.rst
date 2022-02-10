Para configurar este módulo es necesario:

En la compañía:

* Ver descripción módulo l10n_es_ticketbai_api
* Certificado AEAT, dar de alta en la configuración de certificados AEAT en facturación

Posición fiscal:

* Claves de regímenes de IVA (se pueden configurar hasta tres)
* Código de exención de IVA para un IVA en particular

Diario

* Permitir cancelación de asientos (habilita el envío del fichero de anulación al cancelar una factura)

* Habilitar/deshabilitar envio de facturas TicketBAI por diarios de ventas

  * En caso de que se tengan varias series de facturación, si una de ellas se envía a TicketBAI a través de otro software, en el diario de ventas en el cual se contabilizan estas facturas en Odoo deberá estar desactivado el envío de facturas TicketBAI para evitar duplicar la información en hacienda.

Clientes

* Tipo de identificación fiscal (e.g.: NIF-IVA)
