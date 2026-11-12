Para crear un modelo:

1.  Ir a *Facturación \> Declaraciones \> AEAT \> Modelo 216*.
2.  Pulsar en el botón "Crear".
3.  Seleccionar el año y el tipo de período. Las fechas incluidas se
    calculan automáticamente.
4.  Seleccionar el tipo de declaración.
5.  Rellenar el teléfono de contacto, necesario para la exportacion BOE.
6.  Guardar y pulsar en el botón "Calcular".
7.  Rellenar (si es necesario) aquellos campos que Odoo no calcula
    automáticamente:
    - Ejercicios anteriores a 2024:
      - Resultados a ingresar anteriores: \[06\]
    - Ejercicios 2024 y siguientes:
      - Rentas sometidas a retención/ingreso a cuenta:
        - Dividendos y otras rentas de participación en fondos propios de entidades: [05] Número de rentas, [08] Base de retenciones e ingresos a cuenta y [11] Retenciones e ingresos a cuenta.
      - Rentas no sometidas a retención/ingreso a cuenta:
        - Dividendos y otras rentas de participación en fondos propios de entidades: [14] Número de rentas y [17] Base de retenciones e ingresos a cuenta.
      - [20] Resultados a ingresar de anteriores declaraciones por el mismo concepto, ejercicio y período
    - El número de rentas es el de facturas o asientos con retención del
      período; las rectificativas corrigen la base pero no suman rentas.
    - Las rentas exentas por convenio o por normativa interna (retenciones
      "exento por convenio" al 0 %) se calculan como rentas no sometidas a
      retención: \[04\] y \[05\] antes de 2024, \[15\] y \[18\] desde
      2024. Si hay otras rentas no sometidas sin esos impuestos, se suman a
      mano tras calcular.
8.  Cuando los valores sean los correctos, pulsar en el botón
    "Confirmar"
9.  Podemos exportar en formato BOE para presentarlo telemáticamente en
    el portal de la AEAT
