.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===========================================================
Módulo base para modelos relacionados con la TGSS de España
===========================================================

Este módulo permite tener ciertos campos que se requieren para interactuar con
la Tesorería General de la Seguridad Social española en diversos modelos.

Instalación
===========

Este módulo tan solo tiene utilidad cuando es usado como base para otros
módulos, en combinación con los mismos.

Por tanto, **no necesita instalar este módulo.** Si le hace falta para algo en
su sistema, será instalado automáticamente.

Configuración
=============

Las tablas de grupos de cotización, categorías profesionales y niveles de
estudios pueden ser editadas por quien tenga permisos de *Administración /
Configuración* y *Características técnicas*.

Cuando tenga esos permisos, debe acceder a *Ventas > Configuración > Libreta de
direcciones*, y ahí escoger cualquiera de las opciones disponibles:

* Grupos de cotización.
* Categorías profesionales.
* Niveles de estudios.

Documentación para desarrolladores
==================================

Este módulo proporciona clases abstractas para:

* Códigos de cuenta de cotización, o CCC (*contribution_account*).
* Grupos de cotización (*contribution_group*).
* Categoría profesional (*professional_category*).
* Nivel de estudios (*study_level*).
* Todo eso junto (*FullABC*).

También proporciona una base para hacer tests de los códigos de cuenta de
cotización, que deberá heredar para comprobar que su submódulo funciona bien.

Lea el código, está todo documentado.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/189/8.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/
l10n-spain/issues>`_. In case of trouble, please check there if your issue has
already been reported. If you spotted it first, help us smashing it by
providing a detailed and welcomed feedback `here <https://github.com/OCA/
l10n-spain/issues/new?body=module:%20 l10n_es_tgss_base%0Aversion:%20
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
