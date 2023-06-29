Módulo que calcula el impuesto al plástico Mod592.

Esto módulo introduce el menú "AEAT 592 Model" en Contabilidad -> Informe ->
Declaraciones AEAT -> AEAT 592 Model.

Es posible visualizar e imprimir por separado:

* Registro de asientos con productos en impuestos al plástico de los asquirientes

Es posible exportar los registros a archivo con extensión csv para subir a la web de la AEAT.


Known issues / Roadmap
======================

* Los movimientos que involucran adquisicion de plastico no recicable no se
  buscan por su fecha de factura, o día 15 del mes siguiente como muy tarde.
  Solo se buscan en la fecha en que el movimiento quedó realizado.
* No se contempla el caso de Fabricantes. Requiere dependencia de mrp, y tener
  una fuerte trazabilidad de cada quant para contemplar todos los casos de la ley