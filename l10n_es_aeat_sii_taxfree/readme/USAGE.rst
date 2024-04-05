1. Contabilizar devolución de IVA

Contabilizaremos una rectificativa de cliente por cada ticket, indicando el mismo valor que el ticket original. Con ello, anulamos la venta del TPV. En la rectificativa:

Establacer la posición fiscal creada en el apartado de configuración.
Forzar número para que sea el iAEAT o ILR que nos indiquen en el documento nuestro proveedor de servicios Tax Free (agencia que tiene potestad para hacer efectivas las devoluciones de IVA)
El cliente será el intermediario.

En el directorio *static/description* se puede encontrar el fichero *SII_devolucion_IVA_viajeros.csv* con el contenido que se envía al SII.

1. Contabilizar base imponible exportación
En paralelo, es necesario contabilizar un asiento que no se envíe al SII y que dé de alta la base imponible del IVA de exportación. Es decir, si en el paso 2 la rectificativa:

Base imponible: 106,61€
IVA 21%: 22,39€

El asiento tendrá valor de 106,21€, cuenta 70020000 e impuesto "0% Exportación".
Nota: Esto último lo hacemos para que cuadre la contabilidad, el 303 y el SII (pre-303). Cuando contabilizamos la rectificativa del punto 1, el SII lo interpreta como una rectificativa sustitutiva.