* Es necesario añadir el correo electrónico al que notificar los cambios de
  estado en la empresa
* Se debe configurar el servidor de envío
* Por defecto se añado el servicio web de test:
  https://se-face-webservice.redsara.es/facturasspp2
* Si queremos añadir el de producción, debemos cambiar el parámetro por
  https://webservice.face.gob.es/facturasspp2 y modificar el certificado en
  parámetros de sistema

Para poder enviar correctamente, debemos subir el certificado al entorno correspondiente,
para ello, accederemos a https://face.gob.es (Producción) o https://se-face.redsara.es
(Desarrollo).
Allí, accederemos a `Integradores/Gestión de certificados` y nos loguearemos con
Certificado Electrónico.
Una vez dentro, debemos darnos de alta como integrador creando una incidencia en la URL que nos aparecerá.
El siguiente `documento <https://administracionelectronica.gob.es/PAe/FACE/altaintegrador>`_ tiene toda la información detallada.

Cuando nos confirmen el alta, será necesario subir la parte pública de nuestro certificado, un comando para exportarlo es:

.. code-block:: bash

    openssl pkcs12 -in MI_CERTIFICADO.pfx -out MI_CERTIFICADO.crt -nokeys -clcerts
    cat MI_CERTIFICADO.crt

Deberemos añadir toda la parte entre `-----BEGIN CERTIFICATE-----` y
`-----END CERTIFICATE-----` incluidos ambos.
