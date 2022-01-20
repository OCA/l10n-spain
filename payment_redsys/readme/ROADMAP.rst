De acuerdo a los requisitos de Redsys, el tamaño máximo del número de pedido
resultante (``Ds_Order``) es de 12 caracteres. Este addon trunca dicho
dato en el comienzo de la transacción, con el resultado de que, aunque Redsys
la aceptará, no se finalizará el pedido pedido en Odoo al retornar y entregará
un Error 500 a Redsys.
Para evitar esto, es recomendable seleccionar secuencias de pedido que se
ajusten a esta limitación, en particular de 10 o menos caracteres, al ser la
referencia un número extendido a partir del pedido, que incluye un guion y un
número secuencial para posibles repeticiones de pago.
