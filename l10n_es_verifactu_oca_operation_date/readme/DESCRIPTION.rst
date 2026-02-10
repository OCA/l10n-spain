Este módulo extiende la funcionalidad de VERI*FACTU para manejar correctamente las fechas de operación (FechaOperacion) en facturas de cliente y rectificativas.

**Características**

* Incluye la fecha de operación (FechaOperacion) en el XML de VERI*FACTU cuando la
  fecha contable difiere de la fecha de factura.
* Valida que la fecha de operación no pueda ser posterior a la fecha de factura.

**Detalles Técnicos**

El módulo extiende el modelo `account.move` para:

1. Sobrescribir `_get_verifactu_invoice_dict_out()` para incluir el campo FechaOperacion
   cuando la fecha contable (`date`) difiere de la fecha de factura (`invoice_date`).

2. Sobrescribir `_check_verifactu_configuration()` para añadir validación que impide que
   la fecha de operación sea posterior a la fecha de factura.

El campo de fecha de operación solo se incluye cuando:
- Tanto `date` como `invoice_date` están informados
- Son fechas diferentes
- La factura es de cliente o rectificativa (out_invoice, out_refund)

**Caso de Uso**

En algunos escenarios empresariales, la fecha en que ocurrió la operación puede diferir de
la fecha de factura. Por ejemplo, servicios prestados en un periodo pero facturados en
otro. Este módulo asegura que estos casos se reporten correctamente a la agencia tributaria
a través de VERI*FACTU.
