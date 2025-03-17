Para configurar este módulo es necesario:

1.  En la compañia se almacenan las URLs del servicio SOAP de hacienda.
    Estas URLs pueden cambiar según comunidades
2.  Los certificados deben alojarse en una carpeta accesible por la
    instalación de Odoo.
3.  Preparar el certificado. El certificado enviado por la FMNT es en
    formato p12, este certificado no se puede usar directamente con
    Zeep. Se tiene que extraer la clave pública y la clave privada.

El parámetro del sistema l10n_es_aeat_sii_oca.sii_batch almacena el
número de facturas máximo que se enviarán al SII cada vez que se realice
un envío. El valor por defecto es 50.

En Linux se pueden usar los siguientes comandos:

- Clave pública: "openssl pkcs12 -in Certificado.p12 -nokeys -out
  publicCert.crt -nodes"
- Clave privada: "openssl pkcs12 -in Certifcado.p12 -nocerts -out
  privateKey.pem -nodes"
