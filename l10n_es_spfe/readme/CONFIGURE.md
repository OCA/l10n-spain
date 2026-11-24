1. Configure un certificado digital activo en *Facturación > Configuración > AEAT > Certificados AEAT*
   (proporcionado por `l10n_es_aeat`).
2. Acceda a *Ajustes > Usuarios y compañías > Compañías* y abra la pestaña **SPFE**:
   * Active **SPFE Enabled**.
   * Marque **SPFE Test Environment (PRE)** para operar contra el entorno de pruebas
     (`prewww1.aeat.es` / `prewww10.aeat.es`) o desmárquelo para producción.
   * Si emplea un certificado de sello electrónico, marque **Use Electronic Seal Certificate**.
   * **Auto-Send Full Collection / Payment to SPFE** viene activado por defecto para comunicar
     automáticamente el cobro completo (`SETTLEMENT`) y el pago completo (`PAYMENT`) —así como su
     anulación si se rompe la conciliación— al conciliar el banco o mediante el cron; desmárquelo
     si prefiere revisarlos y enviarlos manualmente mediante el aviso en la factura.
   * Pulse **Auto-configure Spanish Taxes for SPFE** si desea reaplicar el mapeo automático
     de categorías UNECE y claves de régimen sobre los impuestos españoles.
3. Revise en los diarios de venta y compra (*Configuración > Diarios > Ajustes de localización*)
   si deben estar incluidos en SPFE.
