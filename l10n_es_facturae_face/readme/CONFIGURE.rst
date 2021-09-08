* Es necesario añadir el correo electrónico al que notificar los cambios de
  estado en la empresa
* Se debe configurar el servidor de envío
* Por defecto se añade el servicio web de test:
  https://se-face-webservice.redsara.es/facturasspp2
* Si queremos añadir el de producción, debemos cambiar el parámetro por
  https://webservice.face.gob.es/facturasspp2 y modificar el certificado en
  parámetros de sistema
* Para el correcto funcionamiento debe ir a FACe y registrar el certificado.

  Pasos a seguir para registrar su certificado en FACe:

  1. Acceder a https://face.gob.es/
  2. Acceder a "Integradores > Gestión de certificados"
  3. Acceder con un certificado
  4. Registrar el certificado utilizando la clave pública (PEM)

  Cuando el certificado caduque, se deberá de volver a acceder para actualizar el certificado. Para realizarlo, se necesitará la parte pública del certificado.

