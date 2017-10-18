.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

============================================================
Secuencia para facturas separada de la secuencia de asientos
============================================================

Este módulo separa los números de las facturas de los de los asientos. Para
ello, convierte el campo number de 'related' a campo de texto normal, y le
asigna un valor según una nueva secuencia definida en el diario
correspondiente.

Cuando una factura se cancela, tanto el número de la factura como el del
asiento se guardan para que si se vuelve a validar, se mantengan ambos.

Su uso es obligatorio para España, ya que el sistema que utiliza por defecto
Odoo no cumple los siguientes requisitos legales en España:

* Las facturas deben llevar una numeración única y continua.
* Los asientos de un diario deben ser correlativos según las fechas.

Al separar la numeración de las facturas de los asientos, es posible
renumerar los asientos al final del ejercicio (por ejemplo mediante el
módulo *account_renumber*) sin afectar a las facturas.

Instalación
===========

En el momento de la instalación, se auto-configuran las secuencias de facturas
de todos los diarios de todas las compañías españolas existentes, poniendo la
secuencia que había anteriormente en el campo "Secuencia de asiento", y
creándose una nueva secuencia única por compañía para ese campo.

Uso
===

Cuando se valide una factura, la secuencia que se utilizará será la configurada
en el campo "Secuencia de factura" en lugar de la "Secuencia de asiento".

En caso de crear una nueva compañía e instalar un plan contable español, la
creación de los diarios se hará también con las secuencias correctamente
definidas.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/189/11.0

Gestión de errores
==================

Los errores/fallos se gestionan en
`las incidencias de GitHub <https://github.com/OCA/l10n-spain/issues>`_.
En caso de problemas, compruebe por favor si su incidencia ha sido ya
reportada. Si fue el primero en descubrirla, ayúdenos a solucionarla proveyendo
una detallada y bienvenida retroalimentación.

Créditos
========

Contribuidores
--------------

* NaN·Tic
* Pedro M. Baeza <pedro.baeza@tecnativa.com>
* Roberto Lizana <roberto.lizana@trey.es>

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

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
