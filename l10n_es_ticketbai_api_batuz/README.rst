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
https://www.batuz.eus/fitxategiak/batuz/lroe/Batuz_LROE_Especificaciones_Env%C3%ADo_Masivo_V1_0_7.pdf

Alcance de operaciones LROE:

* Operaciones realizadas ALTA (A00) y ANULACIÓN (AN0) de facturas
* Modelos soportados: PF 140 (Libro Registro de Operaciones Económicas (personas físicas) y PJ 240 Libro Registro de Operaciones Económicas (personas jurídicas)
* Anotaciones de subcapitulo 1.1 - Ingresos con factura con Software garante (LROE PF 140)
* Anotaciones de subcapitulo 1.1 - Facturas emitidas con Software garante (LROE PJ 240)

El resto de operaciones y anotaciones del LROE quedan fuera del alcance de este módulo.

**Table of contents**

.. contents::
   :local:

Installation
============

Para instalar esté módulo necesita:

#. El módulo l10n_es_ticketbai_api

Credits
=======

Authors
~~~~~~~

* Binovo IT Human Project S.L.

Contributors
~~~~~~~~~~~~

* Ugaitz Olaizola <uolaizola@binovo.es>

Maintainers
~~~~~~~~~~~

.. image:: /l10n_es_ticketbai_api_batuz/static/src/img/binovo_logo_peque.jpg
   :alt: Binovo IT Human Project SL
   :target: http://www.binovo.es

This module is maintained by Binovo IT Human Project SL.
