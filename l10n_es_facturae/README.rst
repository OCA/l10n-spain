.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=================================================================
Gestión de la facturación electrónica española (Factura-E o FACe)
=================================================================

En virtud de la Ley 25/2013, de 27 de diciembre, de impulso de la factura
electrónica y creación del registro contable de facturas en el Sector Público,
desde el día 15 de enero de 2015 todas las facturas remitidas a las
administraciones públicas tienen que ser electrónicas.
Téngase en cuenta, no obstante, que muchas Administraciones Públicas,
y entre ellas la Administración General del Estado, han hecho uso de la
potestad de exonerar de esta obligación a las facturas de hasta 5.000 euros.
Estas facturas electrónicas se enviarán a través de los puntos generales de
entrada de facturas electrónicas de la administración correspondiente.
Estos puntos generales le permitirán consultar electrónicamente el estado de
tramitación de su factura, una vez remitida. El de la Administración General
del Estado se denomina FACe (www.face.gob.es).
En estas facturas electrónicas habrá que indicar la oficina contable,
el órgano gestor y la unidad tramitadora, para que llegue correctamente
a su destino. La administración le proporcionará estos datos.

Informacion sobre el formato:

* http://www.facturae.gob.es/formato/Documents/EspanolFacturae3_0.pdf
* http://www.facturae.gob.es/formato/Versiones/Esquema_castellano_v3_2_x_17_11_2015_unificado.pdf

Instalación
===========

Este módulo depende del módulo *account_payment_partner* y sus dependencias,
que se encuentran en https://github.com/OCA/bank-payment.

Para generar el archivo XML, hace falta el módulo *report_xml* que se encuentra
en https://github.com/OCA/reporting-engine.

Este módulo añade cambios en las plantillas de impuestos. En caso de
instalarlo sobre una base de datos que ya tenga el plan de cuentas contable
español instalado, habrá que actualizar los impuestos usando el módulo
*account_chart_update*, disponible en
https://github.com/OCA/account-financial-tools.

En el caso de querer firmar el formato FacturaE desde Odoo, debe instalarse la
última versión de xmlsec1, disponible en el repositorio
https://github.com/lsh123/xmlsec, que debe compilarse e instalarse con todas
sus dependencias.
Para que funcione, debe añadirse el parámetro LD_LIBRARY_PATH con el valor
/usr/local/lib.
Posteriormente deberá instalarse la libreria xmlsec de Python.



Configuración
=============

* Es necesario ir a los modos de pago e indicar su correspondencia con los
  códigos de Facturae.
* La dirección a la que se remite la factura de venta que queremos exportar
  debe estar marcada como facturae y debe tener cubiertos los datos de
  Oficina contable, Órgano gestor y Unidad tramitadora.
* Si se desea firmar el xml generado desde Odoo, tenemos que irnos al
  formulario de las compañías y subir el certificado en formato .pfx y
  escribir la contraseña de acceso al certificado.
* Actualizar los impuestos usando

Uso
===

Desde el botón "Más" del formulario de factura, ejecutamos el asistente
denominado "Crear fichero Factura-E"

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/189/10.0

Problemas conocidos / Hoja de ruta
==================================

* No está soportada la exportación de facturas rectificativas.
  Fallan las series.
* El certificado y la contraseña de acceso al certificado no se guardan
  cifrados en la base de datos.
* Ver la posibilidad de exportar varias facturas juntas.
* Soportar formato Factura-E v3.2.1.
* Las facturas con recargo de equivalencia no generan un formato correcto.


Credits
=======

Contributors
------------

* ASR-OSS (http://www.asr-oss.com)
* FactorLibre (http://www.factorlibre.com)
* Tecon (http://www.tecon.es)
* Pexego (http://www.pexego.es)
* Malagatic (http://www.malagatic.es)
* Comunitea (http://www.comunitea.com)
* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
* Javi Melendez <javimelex@gmail.com>
* Enric Tobella <etobella@creublanca.es>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
