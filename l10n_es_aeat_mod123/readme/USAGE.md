Para introducir datos válidos para el modelo:

1.  Realizar una factura de proveedor de los intereses cobrados por la
    empresa o particular prestatario con impuesto "Retenciones 19%
    (préstamos)".
2.  O también puede realizar una factura de proveedor del reparto de
    dividendos con el impuesto "Retenciones 19% (dividendos)".
3.  Validarla.

El modelo 123 suma también la retención "Retenciones IRPF 24%
(Rendimientos del capital)". El modelo 111 de OCA no la incluye.

La retención del 24 % sobre rendimientos del capital es la de la cesión
del derecho de explotación de la imagen fuera de una actividad
económica, que se declara en el modelo 123 (resumen anual 193, clave C).
Odoo core etiqueta este impuesto para su propio informe del modelo 111
(casillas [08] y [09]): quien presente el modelo 111 con el informe de
Odoo core debe dejarlo fuera de ese modelo.

La retención "Retenciones IRPF 19% Consejeros y administradores (Compra
consejero de sociedad)" no se incluye en el modelo 123: es un rendimiento
del trabajo (artículo 101.2 de la Ley del IRPF), que se declara en el
modelo 111 (casillas [01] a [03]) y en el resumen anual 190 (clave E).

Las facturas rectificativas de proveedor con retenciones del modelo 123 restan su
base y su retención en el periodo en que se contabilizan, como en el
modelo 111 de OCA. La rectificación de una renta declarada en un periodo
ya presentado se regulariza rectificando la autoliquidación de ese
periodo: las casillas del modelo no admiten importes negativos, y la
autoliquidación complementaria solo procede cuando resulta una cantidad
mayor a ingresar; si resulta menor, se solicita la rectificación de la
autoliquidación (artículos 120.3 y 221.4 de la Ley General Tributaria).

Para crear una declaración del modelo:

1.  Ir a *Facturación \> Declaraciones \> AEAT \> Modelo 123*.
2.  Pulsar en el botón "Crear".
3.  Seleccionar el ejercicio fiscal y el tipo de período. Los periodos
    incluidos se calculan automáticamente.
4.  Seleccionar el tipo de declaración.
5.  Rellenar el teléfono, necesario para la exportacion BOE.
6.  Guardar y pulsar en el botón "Calcular".
7.  Cuando revise los valores, pulse en el botón "Confirmar".
8.  Se puede exportar la declaración en formato BOE para presentarla
    telemáticamente en el portal de la AEAT.
