Secuencia para facturas separada de la secuencia de asientos
============================================================

Este módulo separa los números de las facturas de los de los asientos. Para
ello, convierte el campo number de 'related' a campo de texto normal, y le
asigna un valor según una nueva secuencia definida en el diario
correspondiente.

Cuando una factura se cancela, tanto el número de la factura como el del
asiento se guardan para que si se vuelve a validar, se mantengan ambos.

Su uso es obligatorio para España, ya que legalmente las facturas deben llevar
una numeración única y continua, lo que no es compatible con el sistema que
utiliza Odoo por defecto.

**AVISO**: Hay que configurar las secuencias correspondientes para todos los
diarios de ventas, compras, abono de ventas y abono de compras utilizados
después de instalar este módulo.
