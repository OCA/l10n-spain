=======================
TicketBAI (API) - BATUZ
=======================

.. |badge1| image:: https://img.shields.io/badge/maturity-Alpha-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Alpha
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

|badge1| |badge2|

Módulo base (API) para la declaración de todas las operaciones de venta realizadas por las personas y entidades
que desarrollan actividades económicas en Bizkaia
https://www.batuz.eus/fitxategiak/batuz/lroe/Batuz_LROE_Especificaciones_Env%C3%ADo_Masivo_V1_0_8.pdf

Alcance de operaciones LROE:

* Operaciones realizadas ALTA (A00) y ANULACIÓN (AN0) de facturas
* Modelos soportados: PF 140 (Libro Registro de Operaciones Económicas (personas físicas) y PJ 240 Libro Registro de Operaciones Económicas (personas jurídicas)
* Anotaciones de subcapitulo 1.1 - Ingresos con factura con Software garante (LROE PF 140)
* Anotaciones de subcapitulo 2.1 - Gastos con factura (LROE PF 140)
* Anotaciones de subcapitulo 1.1 - Facturas emitidas con Software garante (LROE PJ 240)
* Anotaciones de capitulo 2 - Facturas recibidas (LROE PJ 240)

El resto de operaciones y anotaciones del LROE quedan fuera del alcance de este módulo.

**Table of contents**

.. contents::
   :local:

Installation
============

Para instalar esté módulo necesita:

#. El módulo l10n_es_ticketbai_api

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-spain/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed
`feedback <https://github.com/OCA/l10n-spain/issues/new?body=module:%20l10n_es_ticketbai_api_batuz%0Aversion:%2011.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* Binovo IT Human Project S.L.
* Digital5, S.L.

Contributors
~~~~~~~~~~~~

* Ugaitz Olaizola <uolaizola@binovo.es>
* Enrique Martín <enriquemartin@digital5.es>

Maintainers
~~~~~~~~~~~

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

This module is part of the `OCA/l10n-spain <https://github.com/OCA/l10n-spain/tree/11.0/l10n_es_ticketbai_api_batuz>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.
