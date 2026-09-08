* Es necesario añadir el correo electrónico al que notificar los cambios de
  estado en la empresa
* Se debe configurar el servidor de envío
* Por defecto se añado el servicio web de test:
  https://se-api-face.redsara.es
* Si queremos añadir el de producción, debemos cambiar el parámetro por
  https://api.face.gob.es

Para poder enviar correctamente, debemos subir el certificado al entorno correspondiente,
para ello, accederemos a https://face.gob.es (Producción) o https://se-integradores-face.redsara.es/
(Desarrollo).
En la web deberemos loguearno con el certificado digital de la empresa.
La primera vez nos pedirán firmar mediante efirma nuestra autorización.

Una vez dentro, accederemos a "Certificados" y añadiremos nuestro certificado PEM.

Luego, en "Plataforma", crearemos una nueva plataforma de "Envío de facturas" y le asignaremos el certificado creado previamente.

Renovación de Certificados
~~~~~~~~~~~~~~~~~~~~~~~~~~

Cuando renovemos el certificado digital, debemos actualizar el certificado en FACE.
Para ello, accederemos a la web de FACE con el nuevo certificado y en "Certificados" y añadiremos el nuevo.
Luego, en "Plataforma", editaremos la plataforma de "Envío de facturas" y le asignaremos el nuevo certificado creado previamente.
