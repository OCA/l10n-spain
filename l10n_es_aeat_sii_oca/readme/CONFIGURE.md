Para configurar este módulo es necesario:

1.  En la compañia se almacenan las URLs del servicio SOAP de hacienda.
    Estas URLs pueden cambiar según comunidades
2.  Los certificados deben alojarse en una carpeta accesible por la
    instalación de Odoo.
3.  Preparar el certificado. El certificado enviado por la FMNT es en
    formato p12, este certificado no se puede usar directamente con
    Zeep. Se tiene que extraer la clave pública y la clave privada.

El desglose de cada factura sale de los datos españoles de sus impuestos
(pestaña de opciones avanzadas del impuesto): tipo (sujeto, exento, no
sujeto, no sujeto por reglas de localización, inversión del sujeto pasivo,
recargo de equivalencia, retención, DUA, no deducible, REAGYP o ignorar),
causa de exención, bien de inversión y alcance (bienes o servicios). Si el
impuesto no tiene alcance, una línea con productos que son todos servicios
va como prestación de servicios y el resto como entrega de bienes. Los
impuestos de tipo "ignorar" no se comunican, y las líneas en las que todos
sus impuestos lo son (p. ej. suplidos) quedan fuera del importe total.

La clave de registro de la factura, y las adicionales, salen de los códigos
de régimen de sus impuestos (exportación, adquisiciones intracomunitarias,
OSS...) o, si no tienen, del régimen general (01) o del criterio de caja
de la compañía, igual que en el campo de Odoo de la factura. En la posición
fiscal se puede forzar una clave de venta y otra de compra para las
operaciones cuya clave no depende del impuesto (grupo de entidades,
arrendamiento de local de negocio, importación sin DUA...): pasa a ser la
clave principal y las de los impuestos, las adicionales.

El parámetro del sistema l10n_es_aeat_sii_oca.sii_batch almacena el
número de facturas máximo que se enviarán al SII cada vez que se realice
un envío. El valor por defecto es 50.

En Linux se pueden usar los siguientes comandos:

- Clave pública: "openssl pkcs12 -in Certificado.p12 -nokeys -out
  publicCert.crt -nodes"
- Clave privada: "openssl pkcs12 -in Certifcado.p12 -nocerts -out
  privateKey.pem -nodes"
