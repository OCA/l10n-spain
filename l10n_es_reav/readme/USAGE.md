Una vez actualizado el plan contable (Impuestos y Posiciones fiscales),
asignaremos la posición fiscal a los proveedores y clientes del régimen
para cambiar los impuestos de compra y venta en las facturas:

1.  Crear o ir a la ficha de un contacto

2.  Asignar la siguiente posición fiscal en el campo "Posición fiscal"  
    *REAV - Agencias de viajes*

La posición fiscal sustituye los impuestos de IVA general por *IVA
Repercutido incluido REAV* en las ventas y por *IVA Soportado no
deducible REAV* en las compras. Los impuestos REAV solo se aplican con
esta posición fiscal: puestos directamente en un producto, desaparecen de
las facturas con la posición fiscal nacional.

Las operaciones de la agencia que quedan fuera del régimen especial siguen
el régimen general (artículo 146 de la Ley del IVA): la posición fiscal
REAV mantiene los impuestos de las compras de bienes de inversión, con su
deducción normal, y los de las entregas exentas de la propia agencia. Solo
las compras para el viaje pierden la deducción: los gastos generales de la
agencia también siguen el régimen general, así que la posición fiscal REAV
se asigna solo a los proveedores de servicios para el viaje.

En una base de datos que viene de la versión 18.0, donde se ponían los
impuestos REAV en los productos, la migración avisa en el registro de los
productos que los tienen. En ellos hay que poner los impuestos de IVA
general y, en los contactos, la posición fiscal REAV.

Los impuestos REAV llevan la clave de régimen 05 (agencias de viajes), que
pasa a las facturas para el SII y VERI\*FACTU. El impuesto de compra REAV
es de tipo no deducible: el SII envía esas compras con cuota deducible 0.
