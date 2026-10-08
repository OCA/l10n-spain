Cuando se valida una factura, automáticamente genera el registro de envío para verifactu. Cada minuto se enviarán todos aquellos registros pendientes de enviar mediante un cron.

Antes de validar, la factura se comprueba contra el esquema oficial de la Agencia Tributaria, que
viene incluido en el módulo (no hace falta conexión). Si el registro no cumple ese esquema, la
factura no se valida y el mensaje indica qué dato falla. Se comprueba en ese momento porque es el
último en el que la factura todavía se puede corregir: una vez validada es un documento fiscal
cerrado.

La misma comprobación se repite al enviar, para los registros que ya estaban validados. El que no
cumple el esquema se queda fuera del envío y los demás se comunican con normalidad. El documento
que se queda fuera lo indica en su propio formulario, en el campo de error de envío, y se crea un
aviso para el grupo responsable de VERI*FACTU. Mientras no se corrija el dato, ese registro se
reintenta en cada pase del cron.

Para que ese aviso lo vea alguien, el grupo *VERI\*FACTU responsable* tiene que tener usuarios: la
actividad se asigna al primero del grupo y, si el grupo está vacío, al usuario con el que se
ejecuta el cron, que no suele mirarlas. Conviene añadir al grupo a quien vaya a atender los
rechazos antes de empezar a facturar.

En la compañía, la casilla *Omitir la comprobación del esquema al validar* deja de impedir la
validación de la factura. Está pensada para poder seguir facturando mientras se investiga un
rechazo indebido, no como ajuste permanente: el registro que no cumple el esquema se sigue
quedando fuera del envío, así que apagarla no consigue que llegue a la Agencia. El cambio queda
registrado en el historial de la compañía.
