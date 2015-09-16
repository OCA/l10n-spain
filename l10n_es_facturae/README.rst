.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

========
Facturae
========

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

(http://www.facturae.gob.es/factura-electronica/noticias-destacadas/Paginas/obligatoriedad-facturas-electronicas.aspx)

Installation
============

La única dependencia en el caso de querer firmar el formato facturae desde
Odoo es tener instalado el jre de java en el servidor que hospeda al Odoo.

Configuration
=============

* Es necesario ir a los modos de pago e indicar su correspondencia con los
  códigos de FACe
* La dirección a la que se remite la factura de venta que queremos exportar
  debe estar marcada como facturae y debe tener cubiertos los datos de
  Oficina contable, Órgano gestor y Unidad tramitadora.
* Si se desea firmar el xml generado desde Odoo, tenemos que irnos al
  formulario de las compañías y subir el certificado en formato *.pfx y
  escribir la contraseña de acceso al certificado.

Usage
=====

Desde el botón "Más" del formulario de factura ejecutamos el asistente de
nombre "Crear fichero facturae"

Known issues / Roadmap
======================

* No está soportada la exportación de facturas rectificativas.
* Sólo se exportan ivas repercutidos.
* No se controla el ancho de varios campos cuando se exportan.
* El certificado y la contraseña de acceso al certificado no se guardan
  cifrados en la base de datos.
* El fichero exportado debe subirse manualmente a la página de FACe, no está
  implementado el envío por servicio web, ya que tienen que conceder permiso
  expreso.

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

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
