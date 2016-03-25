.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License

===============================================
Plan contable e impuestos de España (PGCE 2008)
===============================================

* Define las siguientes plantillas de cuentas:

  * Plan general de cuentas español 2008.
  * Plan general de cuentas español 2008 para pequeñas y medianas empresas.
  * Plan general de cuentas español 2008 para asociaciones.
* Define plantillas de impuestos para compra y venta.
* Define plantillas de códigos de impuestos.
* Define posiciones fiscales para la legislación fiscal española.

**IMPORTANTE:** Ésta es una versión mejorada con respecto al módulo *l10n_es*
que se encuentra en la versión estándar de Odoo, por lo que es conveniente
instalar ésta para disponer de los últimos datos actualizados.

Historial
---------

* v9.0.1.0.0: Migración a la versión 9.0c de Odoo.
* v8.0.5.4.0: Varias correcciones para el modelo 123 y para las rectificaciones:

  * Códigos de impuestos de retenciones de venta movidos al modelo 200
  * Creados códigos de impuestos para el modelo 123.
  * Creados impuestos de reparto de dividendos y de préstamos.
  * Creados códigos de impuesto para cada uno de los porcentajes y conceptos
    de las rectificaciones.
  * Incluida cuenta 4759.
* v8.0.5.3.0: Añadido "IVA soportado no sujeto".
* v8.0.5.2.0: Añadida retención 19,5% arrendamientos.
* v8.0.5.1.0: Renombrado todo lo relacionado con arrendamientos para no incluir
  la palabra "IRPF", ya que no es como tal IRPF.
* v8.0.5.0: Se ha rehecho toda la parte de impuestos para dar mayor facilidad
  de consulta de los datos para las declaraciones de la AEAT y para cubrir
  todas las casuísticas fiscales españolas actuales. Éstas son las
  características más destacadas:

  * Desdoblamiento de los impuestos principales para bienes y para servicios.
  * Nuevo árbol de códigos de impuestos orientado a cada modelo de la AEAT.
  * Nuevos códigos para los códigos de impuestos para facilitar su
    actualización.
  * La casilla del modelo viene ahora en la descripción, no en el código.
  * Posiciones fiscales ajustadas para el desdoblamiento.
  * Nuevo impuesto y posición fiscal para retención IRPF 19%.
  * Nuevo impuesto para revendedores con recargo de equivalencia.
  * Nuevas posiciones fiscales para retenciones de arrendamientos.
  * Pequeños ajustes en cuentas contables.
* v8.0.4.1.0: Cambio en el método que obtiene el nombre del impuesto e
  intercambiados los campos descripción/nombre para que no aparezca los códigos
  en documentos impresos ni en pantalla.
* v8.0.4.0.0: Refactorización completa de los planes de cuentas, con las
  siguientes caracteristicas:

  * Creacion de un plan común a los tres planes existentes, que reúne las
    cuentas repetidas entre ellos.
  * Eliminación de la triplicidad de impuestos y de códigos de impuestos.
  * Asignación de códigos a los impuestos para facilitar su actualización.
  * Eliminación de duplicidad de tipos de cuentas.

Instalación
===========

Si en la base de datos a aplicar ya se encuentra instalado el plan contable de
la compañía, será necesario actualizarlo con el módulo *account_chart_update*,
disponible en https://github.com/OCA/account-financial-tools.

Créditos
========

Contribuidores
--------------
* Jordi Esteve <jesteve@zikzakmedia.com>
* Dpto. Consultoría Grupo Opentia <consultoria@opentia.es>
* Ignacio Ibeas <ignacio.ibeas@acysos.com>
* Pablo Cayuela <pablo.cayuela@aserti.es>
* Carlos Liébana <carlos.liebana@factorlibre.com>
* Hugo Santos <hugo.santos@factorlibre.com>
* Albert Cabedo <albert@gafic.com>
* Pedro M. Baeza <pedro.baeza@tecnativa.com>

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
