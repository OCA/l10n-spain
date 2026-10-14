Para configurar este módulo es necesario:

#. En la compañia se almacenan las URLs del servicio SOAP de hacienda.
   Estas URLs pueden cambiar según comunidades.
   Hacienda Foral de Navarra no publica WSDL propio: seleccione esa agencia
   en la compañía y, en la ficha de la agencia (pestaña SII), indique a mano
   las URLs SOAP de facturas emitidas y recibidas. El envío usa el WSDL de la
   AEAT y como dirección SOAP esas URLs.
#. Los certificados deben alojarse en una carpeta accesible por la instalación
   de Odoo.
#. Preparar el certificado. El certificado enviado por la FMNT es en formato
   p12, este certificado no se puede usar directamente con Zeep. Se tiene que
   extraer la clave pública y la clave privada.

En Linux se pueden usar los siguientes comandos:

- Clave pública: "openssl pkcs12 -in Certificado.p12 -nokeys -out publicCert.crt -nodes"
- Clave privada: "openssl pkcs12 -in Certifcado.p12 -nocerts -out privateKey.pem -nodes"

Además, el módulo `queue_job` necesita estar configurado de una de estas formas:

#. Ajustando variables de entorno:

     ODOO_QUEUE_JOB_CHANNELS=root:4

   u otro canal de configuración. Por defecto es root:1

   Si xmlrpc_port no está definido: ODOO_QUEUE_JOB_PORT=8069

#. Otra alternativa es usuando un fichero de configuración:

     [options]
     (...)
     workers = 4
     server_wide_modules = web,base_sparse_field,queue_job

     (...)
     [queue_job]
     channels = root:4

#. Por último, arrancando Odoo con --load=web,base_sparse_field,queue_job y --workers más grande que 1.

Más información http://odoo-connector.com
