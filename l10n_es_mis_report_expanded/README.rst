.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

===========================================================================
Plantillas MIS Builder para informes contables españoles, formato expandido
===========================================================================

Incluye las siguientes plantillas para el motor de informes provisto
por el módulo *mis_builder*, mostrando el detalle por cuenta contable:

    * Balance PYMEs (PGCE 2008) - Expandido
    * Cuenta de pérdidas y ganancias PYMEs (PGCE 2008) - Expandido
    * Balance abreviado (PGCE 2008) - Expandido
    * Cuenta de pérdidas y ganancias abreviado (PGCE 2008) - Expandido
    * Balance normal (PGCE 2008) - Expandido
    * Cuenta de pérdidas y ganancias completo (PGCE 2008) - Expandido
    * Estado de ingresos y gastos reconocidos (PGCE 2008) - Expandido

La diferencia con el módulo 'l10n_es_mis_reports' es que estas plantillas
muestran el desglose de todas las cuentas contables, mientras que el anterior
módulo muestra el desglose oficial, excluyendo el detalle a nivel de cuenta
contable.


Instalación
===========
Este módulo depende del módulo 'mis_builder' que puede obtenerse
en https://apps.odoo.com, o bien en https://github.com/OCA/mis-builder.

Configuración
=============

* Acceder a *Contabilidad > Informes > MIS Reports* y crear un informe,
  indicando los periodos deseados, y usando una de las plantillas
  proporcionadas por este módulo.

El informe sólamente considera las cuentas numeradas de acuerdo con el
formato establecido por el PGCE.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/119/10.0


Incidencias
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-belgium/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/l10n-spain/issues/new?body=module:%20l10n_be_mis_reports%0Aversion:%2010.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Créditos
========

Contribuidores
--------------

* Jordi Ballester (EFICENT) <jordi.ballester@eficent.com>


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
