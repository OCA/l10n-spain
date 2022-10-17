==============
AEAT Base CRLF
==============

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Este módulo añade la posibilidad de terminar las líneas en los modelos AEAT
con salto de línea. Necesario para alguna haciendas forales.
Probado en la Comunidad Foral de Navarra y Gipuzkoa.

Installation
============

Módulos necesarios:
* l10n_es_aeat: https://www.odoo.com/apps/modules/13.0/l10n_es_aeat/



Configuration
=============

En Facturación -> Configuración -> AEAT -> Configuración de Exportación a BOE

Editar el modelo deseado y activar en la línea deseada del registro, la opción “Line CRLF”.

P.ej. en el modelo 349, el registro es de 500 caracteres.

Para añadir el CRLF en el sitio correcto, editar la línea “Sello electrónico (en blanco)” que inicia en la posición 488 y termina en la 500. Activar el campo “Line CRLF”. Guardar y exportar el fichero BOE.


Usage
=====

No tiene uso especial, solo exportar el modelo.


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-spain/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed
`feedback <https://github.com/OCA/l10n-spain/issues/new?body=module:%20l10n_es_aeat_line_crlft%0Aversion:%2013.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.


Credits
=======

Authors
~~~~~~~

* Acysos S.L.

Contributors
------------

* Ignacio Ibeas - Acysos S.L. <ignacio@acysos.com>


Maintainer
----------

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

This module is part of the `OCA/l10n-spain <https://github.com/OCA/l10n-spain/tree/13.0/l10n_es_aeat>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.
