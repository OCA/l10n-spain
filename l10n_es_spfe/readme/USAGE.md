* **Emisión y remisión al SPFE**:
  1. Valide una factura de cliente con fecha igual o posterior al 06/10/2026.
  2. En entorno de pruebas (PRE), puede pulsar **Validate SPFE (PRE)** para verificar la factura
     contra `ValidationInvoiceSOAP` sin registrarla.
  3. Pulse **Send to SPFE** (o utilice la acción masiva en la vista lista / tarea programada)
     para remitir la factura y obtener el localizador SPFE (`LOCGENV1:...`).
* **Estados comerciales y de pago/cobro (Anexo II)**:
  * Al quedar una factura de cliente o de proveedor conciliada y pagada al 100 % (`payment_state = paid`),
    si **Auto-Send Full Collection / Payment to SPFE** está activo (valor por defecto), Odoo comunica
    automáticamente `SETTLEMENT` (cobro completo) o `PAYMENT` (pago completo) tomando la fecha real del
    apunte conciliado (y `CANCELSETTLEMENT` / `CANCELPAYMENT` si se deshace la conciliación), con reintento
    por cron en caso de incidencia temporal. Si está en modo manual, muestra una alerta en la factura con el
    botón directo **Comunicar cobro/pago a SPFE** (también disponible de forma masiva en **Acción**).
  * Desde **Acción > Evento de estado SPFE** puede comunicar en cualquier momento `PAYMENT`, `REJECTION`,
    `SETTLEMENT`, `DEFAULT` o sus anulaciones indicando opciones avanzadas (acuerdo de financiación, fechas de recepción, etc.).
* **Consulta y descarga de facturas recibidas**:
  * Desde *Facturación > Informes > AEAT > SPFE (Factura Electrónica) > Query / Download SPFE Invoices*,
    consulte facturas por rango de fechas y descargue automáticamente las facturas UBL recibidas
    creando facturas de proveedor en borrador (o vinculándolas si ya estaban registradas).
  * Desde **Acción > Descargar UBL de SPFE (por ID)** en cualquier factura contabilizada puede recuperar
    y adjuntar su XML UBL 2.5 oficial mediante `DownloadInvoicesByIDSOAP`.
