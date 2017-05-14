
.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Pasarela de pago Redsys
=======================

Este módulo añade la opción de pago a través de la pasarela de Redsys.

Instalación
===========

Para utilizar este módulo, necesita la biblioteca `pycrypto
<https://pypi.python.org/pypi/pycrypto>`_ instalada en su sistema::

    pip install pycrypto

Configuración
=============

Parámetros
----------

* **Nombre del comercio**: Indicaremos el nombre del comercio.

* **Número de comercio (FUC)**: Indicaremos el número de comercio que
  nuestra entidad nos ha comunicado.

* **Clave secreta de encriptación**: Indicaremos la clave de encriptación
  que tiene el comercio.

* **Número de terminal**: Indicaremos el terminal del TPV.

* **Tipo de firma**: Seleccionaremos el tipo de firma del comercio.

* **Tipo de moneda**: Seleccionaremos la moneda de nuestro terminal TPV
  (Normalmente EUR - Euros).

* **Tipo de transacción**: Indicaremos el tipo de transacción, 0.

* **Idioma TPV**: Indicaremos el idioma en el TPV.

* **URL_OK/URL_KO**: Durante el proceso del pago, y una vez que
  se muestra al cliente la pantalla con el resultado del mismo, es
  posible redirigir su navegador a una URL para las transacciones
  autorizadas y a otra si la transacción ha sido denegada. A éstas
  se las denomina URL_OK y URL_KO, respectivamente. Se trata
  de dos URLs que pueden ser proporcionadas por el comercio.

* **Porcentaje de pago**: Indicar el porcentaje de pago que se permite, si
  se deja a 0.0 se entiende 100%

Nota
----

Se tiene que verificar la configuración del comercio en el
módulo de administración de Redsys, donde la opción “Parámetros en las
URLs” debe tener el valor “SI”.

En caso de que exista más de una base de datos en la instalación, cuando la
pasarela de pago envía el formulario a "/payment/redsys/return" odoo no sabe
con que base de datos procesar esta información.
Por lo que hay que establecer los parametros **dbfilter** y **dbname** en
**openerp-server.conf**.

Créditos
========

Contribuidores
--------------

* Sergio Teruel <sergio.teruel@tecnativa.com>
* Carlos Dauden <carlos.dauden@tecnativa.com>

Financiadores
-------------
La migración de este módulo forma parte de una campaña de migración de la
localización española que ha sido posible gracias a la colaboración económica
de las siguientes empresas (por orden alfabético):

* `Aizean evolution <http://www.aizean.com>`_
* `Aselcis consulting <https://www.aselcis.com>`_
* `AvanzOSC <http://avanzosc.es>`_
* `Diagram software <http://diagram.es>`_
* `Domatix <http://www.domatix.com>`_
* `Eficent <http://www.eficent.com>`_
* `FactorLibre <http://factorlibre.com>`_
* `Fairhall solutions <http://www.fairhall.es>`_
* `GAFIC SLP <http://www.gafic.com>`_
* `Incaser <http://www.incaser.es>`_
* `Ingeos <http://www.ingeos.es>`_
* `Nubistalia <http://www.nubistalia.es>`_
* `Punt sistemes <http://www.puntsistemes.es>`_
* `Praxya <http://praxya.com>`_
* `Reeng <http://www.reng.es>`_
* `Soluntec <http://www.soluntec.es>`_
* `Tecnativa <https://www.tecnativa.com>`_
* `Trey <https://www.trey.es>`_
* `Vicent Cubells <http://vcubells.net>`_

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
