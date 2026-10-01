Cuando falla el encadenamiento de un pedido de TPV ya cobrado, la venta no se
interrumpe: el pedido queda marcado y se localiza con el filtro «VERI*FACTU
failed» en Punto de venta > Pedidos, con el error a la vista en su pestaña
VERI*FACTU.

Los pedidos pendientes los encadena la acción planificada «Generar el
encadenamiento VERI*FACTU pendiente de los pedidos de TPV», que se ejecuta
cada diez minutos y toma primero los más antiguos, de modo que entran en la
cadena en el orden en que se cobraron.

El botón «Generar encadenamiento VERI*FACTU» de la ficha del pedido hace lo
mismo para un pedido suelto. Es la vía de vuelta para un pedido que haya
agotado los intentos, porque el botón no mira ese contador.
