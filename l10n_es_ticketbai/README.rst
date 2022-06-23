==========================
TicketBAI - Gobierno Vasco
==========================

.. |badge1| image:: https://img.shields.io/badge/maturity-Alpha-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-OCA%2Fl10n--spain-lightgray.png?logo=github
    :target: https://github.com/OCA/l10n-spain/tree/11.0/l10n_es_ticketbai
    :alt: OCA/l10n-spain

|badge1| |badge2| |badge3|

Módulo para la declaración de todas las operaciones de venta realizadas por las personas y entidades
que desarrollan actividades económicas
https://www.euskadi.eus/contenidos/informacion/ticketbai/es_14815/adjuntos/TicketBAI_Especificaciones_v_1_1.pdf

**Table of contents**

.. contents::
   :local:

Installation
============

Para instalar este módulo se necesita:

#. Los módulos `l10n_es_ticketbai_api`, `l10n_es_aeat`, `l10n_es_aeat_certificate`, `account_cancel`

y el módulo `account_invoice_tax_required` que se encuentra en:

https://github.com/OCA/account-invoicing

Configuration
=============

Ver descripción módulo `l10n_es_ticketbai_api`.

Para configurar este módulo es necesario:

En la compañía:

* Certificado AEAT, dar de alta en la configuración de certificados AEAT en facturación

Posición fiscal:

* Claves de regímenes de IVA (se pueden configurar hasta tres)
* Código de exención de IVA para un IVA en particular

Diario

* Permitir cancelación de asientos (habilita el envío del fichero de anulación al cancelar una factura)

Clientes

* Tipo de identificación fiscal (e.g.: NIF-IVA)


Usage
=====

* Factura de cliente

  * Se genera el fichero y se firma al validar la factura.
* Factura de cliente simplificada: marcando el cliente como cliente anónimo

  * Se genera el fichero como factura simplificada
  * No se envían datos del cliente
* Factura de cliente rectificativa

  * Diferencias (total o parcial)

    * Parcial: se genera el fichero y se firma al validar la factura rectificativa. La factura se ha tenido que generar desde el asistente de emitir rectificativa
    * Total: se genera el fichero y se firma al crear la rectificativa desde el asistente de emitir rectificativa, escogiendo la opción `cancelar`
  * Sustitución (sólo soportado en caso de sustituir a una factura simplificada)

    * Se genera el fichero y se firma al validar la factura. La factura se ha tenido que generar desde el asistente de emitir rectificativa
* Anulación de factura

  * Se genera el fichero y se firma al cancelar una factura validada


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-spain/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed
`feedback <https://github.com/OCA/l10n-spain/issues/new?body=module:%20l10n_es_ticketbai%0Aversion:%2011.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* Binovo IT Human Project S.L.

Contributors
~~~~~~~~~~~~

* Victor Laskurain <blaskurain@binovo.es>
* Luis J. Salvatierra <ljsalvatierra@binovo.es>
* Aritz Olea <ao@landoo.es>

Maintainers
~~~~~~~~~~~

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

This module is part of the `OCA/l10n-spain <https://github.com/OCA/l10n-spain/tree/11.0/l10n_es_ticketbai>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.
