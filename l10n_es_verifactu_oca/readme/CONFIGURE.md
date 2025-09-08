Para configurar este módulo es necesario:

1.  Acceder a Facturación/Contabilidad -\> Configuración -\> AEAT -\>
    Agencia Tributaria, podrás consultar las URLs del servicio SOAP de
    Hacienda. Estas URLs pueden cambiar según comunidades
2.  El certificado enviado por la FMNT es en formato p12, este
    certificado no se puede usar directamente con Zeep. Accede a
    Facturación/Contabilidad -\> Configuración -\> AEAT -\> Certificados
    AEAT, y allí podrás: Subir el certificado p12 y extraer las claves
    públicas y privadas con el botón "Obtener claves"
3.  Debes tener en cuenta que los certificados se alojan en una carpeta
    accesible por la instalación de Odoo.
4.  Completar los datos de desarrollador y del encadenamiento a nivel de
    compañía en la pestaña de VERI\*FACTU.

En caso de que la obtención de claves no funcione y uses Linux, cuentas
con los siguientes comandos para tratar de solucionarlo:

- Clave pública: "openssl pkcs12 -in Certificado.p12 -nokeys -out
  publicCert.crt -nodes"
- Clave privada: "openssl pkcs12 -in Certificado.p12 -nocerts -out
  privateKey.pem -nodes"

1.  Establecer en las posiciones fiscales la clave de impuestos y la
    clave de registro VERI\*FACTU.
2.  Para aplicar las claves ejecute el asistente de actualización del
    módulo accountchart_update.
