Para configurar este módulo necesitas:

#. En la compañia se almacenan las URLs del servicio SOAP de hacienda.
   Estas URLs pueden cambiar según comunidades
#. Los certificados deben alojarse en una carpeta accesible por la instalación
   de Odoo.
#. Preparar el certificado. El certificado enviado por la FMNT es en formato
   p12, este certificado no se puede usar directamente con Zeep. Se tiene que
   extraer la clave pública y la clave privada.

En Linux se pueden usar los siguientes comandos:

- Clave pública: "openssl pkcs12 -in Certificado.p12 -nokeys -out publicCert.crt -nodes"
- Clave privada: "openssl pkcs12 -in Certifcado.p12 -nocerts -out privateKey.pem -nodes"

Connector:

#. Ajustar variables de entorno:

     ODOO_CONNECTOR_CHANNELS=root:4

   u otro canal de configuración. Por defecto es root:1

   Si xmlrpc_port no esta definido: ODOO_CONNECTOR_PORT=8069

#. Otra alternativa es usuando un fichero de configuración:

     [options]
     (...)
     workers = 4
     server_wide_modules = web,web_kanban,connector

     (...)
     [options-connector]
     channels = root:4

#. Arranca Odoo con --load=web,web_kanban,connector y --workers más grande que 1.

Más información http://odoo-connector.com
