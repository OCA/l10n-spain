* Exporta el certificado público en formato pem usando,por ejemplo, el siguiente código:
  `openssl pkcs12 -in MI_CERTIFICADO.p12 -out newfile.pem -clcerts -nokeys`
* Instala @firma
* Accede a  faceb2b https://faceb2b.gob.es/portal
* Accede como cliente usando el certificado en el navegador
* En caso de no existir el DIRe, el sistema nos solicitará crearlo.
  Debemos aceptar y realizar los pasos en la web a la que nos envían.
* Acepta las condiciones como cliente
* Deslogeate y vuelve a entrar como Empresa de Servicios de facturación (ESF)
* Acepta las condiciones y crea la ESF. No es necesario marcar que damos servicios a terceros.
* Crea una plataforma añadiendo el certificado público creado anteriormente
* Ve a la pestaña Alta de Clientes
* Cambia a `Mis Unidades`
* Selecciona el DIRe de la empresa como cliente y asignale la plataforma que has creado

Tras todos estos pasos, el envío y la recepción de facturas ya debería estar creado.
