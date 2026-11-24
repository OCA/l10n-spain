Este módulo permite integrar Odoo con la **Solución Pública de Facturación
Electrónica (SPFE)** de la Agencia Estatal de Administración Tributaria (AEAT),
conforme al Real Decreto 238/2026 y la Orden HAC/1028/2026 (Ley Crea y Crece).

Funcionalidades principales:

* Generación y validación contra esquema XSD oficial de facturas electrónicas
  en formato **UBL 2.5** adaptadas al modelo semántico **EN 16931:2026** y al
  **Anexo I** del SPFE (`urn:cen.eu:en16931:2026#conformant#urn:aeat.es:spfe:1.0.0:extended`),
  reutilizando los módulos oficiales de OCA (`base_ubl`,
  `base_ubl_parse`, `l10n_es_aeat`, `account_tax_unece`, `account_payment_unece`
  y `uom_unece`).
* Soporte completo de particularidades fiscales españolas: claves de régimen
  (`IVA`, `IGIC`, `IPSI`), recargo de equivalencia (`N`), retenciones de IRPF
  (`WithholdingTaxTotal` + `CollectionInvoiceLine` `RETE`), suplidos (`SUPL` / `MINO`),
  exenciones (`VATEX-EU` y `VATEX-ES`), facturas rectificativas por diferencias
  (`I`) y por sustitución (`S`), integración automática con QR de VERI*FACTU /
  TicketBAI e inmuebles (`RCAT`).
* Transporte **SOAP 1.2 + ebMS 3.0 (AS4)** con adjuntos MIME `multipart/related`
  autenticado mediante los certificados X.509 de `l10n_es_aeat` (tanto puerto de
  certificado personal/representante como puerto de sello electrónico).
* Integración de los 9 servicios web del catálogo SPFE:
  1. Remisión de facturas (`SendInvoiceSOAP` / `SUBMITINVOICE`) en lotes de hasta 100.
  2. Anulación de facturas (`CancelInvoiceSOAP` / `CANCELINVOICE`).
  3. Consulta por identificador (`GetInvoicesSOAP` / `QUERYBYID`).
  4. Consulta por filtro de fechas con paginación (`GetRegisteredInvoiceSOAP` / `QUERYBYFILTER`).
  5. Descarga de facturas por identificador (`DownloadInvoicesByIDSOAP` / `DOWNLOADBYID`).
  6. Descarga e importación de facturas de proveedor por localizador (`DownloadInvoicesByLOCSOAP` / `DOWNLOADBYLOC`).
  7. Comunicación de estados del destinatario — Anexo II (`CustomerInvoiceEventsSOAP`: `PAYMENT`, `CANCELPAYMENT`, `REJECTION`, `CANCELREJECTION`).
  8. Comunicación de estados del emisor — Anexo II (`SupplierInvoiceEventsSOAP`: `SETTLEMENT`, `CANCELSETTLEMENT`, `DEFAULT`, `CANCELDEFAULT`).
  9. Validación previa individual en entorno PRE (`ValidationInvoiceSOAP`).
