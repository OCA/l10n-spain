.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

======================================================
Campos de la TGSS española en los contactos y empresas
======================================================

Este módulo añade los siguientes campos a las empresas y contactos
(``res.partner``):

* Códigos de cuenta de cotización, o CCC.
* Campos tan sólo para contactos (no empresas):
    * ¿Afectado/a por terrorismo?
    * ¿Afectado/a por violencia de género?
    * Porcentaje de discapacidad.
    * Grupo de cotización.
    * Categoría profesional.
    * Nivel de estudios.

Son campos que suelen ser necesarios para interactuar con la Tesorería General
de la Seguridad Social de España, en determinadas circunstancias.

Configuración
=============

Vea la documentación de configuración del módulo ``l10n_es_tgss_base``.

Uso
===

Los campos los encontrarás en la ficha de cada empresa. En el caso de ciertos
campos, tan sólo están disponibles para los contactos (cuando *no* es una
empresa).

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/189/8.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/
l10n-spain/issues>`_. In case of trouble, please check there if your issue has
already been reported. If you spotted it first, help us smashing it by
providing a detailed and welcomed feedback `here <https://github.com/OCA/
l10n-spain/issues/new?body=module:%20 l10n_es_tgss_partner%0Aversion:%20
8.0.1.0.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Jairo Llopis <j.llopis@grupoesoc.es>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
