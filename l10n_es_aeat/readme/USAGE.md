Para poder visualizar un archivo BOE, hay que:

1.  Entrar en *Facturación \> Configuración \> AEAT \> Configuración de
    exportación a BOE*.
2.  Entrar en el detalle de la configuración de exportación principal
    para el modelo.
3.  Pulsar en el smart-button "Comparar archivo".
4.  Seleccionar el archivo correspondiente y pulsar en "Comparar".
5.  Aparecerá una ventana con cada una de las líneas de exportación, la
    cadena correspondiente a dicha línea, y si es un importe numérico,
    su cifra asociada.

Para importar el certificado, hay que:

1.  Entrar en *Facturación \> Configuración \> AEAT \> Certificados*
2.  Crear uno nuevo. Rellenas los datos del formulurio y subir el
    archivo p12
3.  Pulsar obtener claves e introducir la contraseña del certificado

Para gestionar inmuebles, hay que:

1.  Entrar en *Facturación \> Configuración \> AEAT \> Inmuebles*
2.  Crear uno nuevo, rellenando los datos del formulario.
3.  Ya se podrá añadir un inmueble en el campo Inmueble de las lineas de factura.

En las líneas se pueden elegir los inmuebles del contacto de la factura
(como el arrendador de una factura recibida) y los de la propia
compañía (como el local que alquila al cliente). La referencia catastral se valida
con los dígitos de control de la Dirección General del Catastro, salvo
en País Vasco, Navarra y en el extranjero, que tienen otro formato.

Para los modelos 180 y 347 hay que indicar el código INE del municipio
(las dos cifras de la provincia y las tres del municipio, que se pueden
consultar en el Instituto Nacional de Estadística). El campo Municipio
solo hace falta si la ciudad es una localidad de otro municipio.

## Identificación de clientes para la AEAT

Introduzca los documentos en el apartado nativo **Identificadores adicionales** de
la ficha del contacto. El módulo utiliza estos mismos datos para la identificación
de la AEAT, evitando duplicar campos de documento en la pestaña AEAT.

La prioridad es el NIF español o un VAT comunitario válido. En los demás casos,
se utiliza el primer identificador nativo disponible, en este orden: pasaporte,
documento extranjero o VAT, certificado de residencia y otro documento. Un VAT
sin formato comunitario válido puede servir como documento extranjero según la
validación fiscal existente.

Para validar una identificación se requiere un VAT útil o uno de esos documentos.
El valor `NO_DISPONIBLE` y un contacto extranjero sin documento no acreditan una
identificación válida.

Durante la actualización desde la versión anterior, los tipos heredados 03, 05 y
06 se copian a su clave nativa cuando está vacía. Si hay datos incompletos, un tipo
no convertible o un valor nativo distinto, la actualización continúa; conserva las
columnas heredadas para conciliación y registra el contacto y el motivo en el log,
sin incluir el documento personal.
