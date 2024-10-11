Configuración básica
~~~~~~~~~~~~~~~~~~~~

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

Si además queremos configurar la detección automática de DIRe, deberemos acceder a la web https://dire.gob.es/portal/integracionws
y darse de alta como API de Consumo. Nos devolverá una clave, que deberemos configurar en un parámetro de sistema con clave `dire.ws.apikey`.

Envío de facturas
~~~~~~~~~~~~~~~~~

Para configurar el envío, de un cliente haremos lo siguiente:

* accedemos al cliente
* vamos a la pestaña Facturación / Contabilidad
* marcamos facturae, y configuramos tipo de envío faceb2b. Será necesario rellenar el campo DIRe

Si queremso ir más rápido, podemos usar la API de de DIRe. Para ello, haremos lo siguiente:

* accedemos al cliente
* vamos a la pestaña Facturación / Contabilidad
* Apretamos el botón Check faceb2b

Recepción de facturas
~~~~~~~~~~~~~~~~~~~~~

Para recibir facturas directamente desde FACeB2B, debemos realizar los siguientes pasos:
* Acceder a `Facturación / Configuración / Contabilidad / Diarios Contables`
* Seleccionamos el diario de compras en el que queremos recibir las facturas
* En la pestaña `Configuración Avanzada` podremos marcar el `Importar FACeB2B` y el DIRe que vamos a usar.

La parte de recepción sólo tiene sentido si tenemos instalado el módulo `l10n_es_facturae_import`.
