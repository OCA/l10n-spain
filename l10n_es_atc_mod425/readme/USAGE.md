1.  Ir a `Contabilidad \> Declaraciones ATC \> Modelo 425`.
2.  Pulsar en el botón `Crear`
3.  Seleccionar el ejercicio fiscal.
4.  Seleccionar el tipo de declaración.
5.  Rellenar el teléfono y teléfono móvil.
6.  Guardar y pulsar en el botón "Calcular"
7.  Rellenar (si es necesario) aquellos campos que Odoo no calcula
    automáticamente.
8.  Cuando los valores sean los correctos, pulsar en el botón
    `Confirmar`
9. El boton `Generar declaración` permite generar el archivo .xml y usando el `.jar` provisto por la ATC se puede obtener la declaracion. Este puede ser en formato `.dec` cuando en el campo `Tipo de salida` se elija `telemático`; en caso contrario, se generará en formato `.pdf`. Con la declaración calculada solo se puede imprimir el borrador (`Tipo de salida` `Imprimir Borrador`); la autoliquidación final y el fichero de la presentación telemática se generan con la declaración confirmada, que antes comprueba los datos que pide el programa de la ATC.
