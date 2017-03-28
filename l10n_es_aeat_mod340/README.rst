.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=====================================================================
Presentación del modelo 340. Exportación a formato AEAT. Libro de IVA
=====================================================================

Incluye las siguientes posibilidades:

* Búsqueda de facturas emitidas y recibidas.
* Exportación a formato de AEAT de facturas emitidas y recibidas.
* Exportación de facturas con varios tipos impositivos. Clave de operación C.
* Facturas intracomunitarias, excepto las operaciones a las que hace
  referencia el artículo 66 del RIVA que tienen un tratamiento especial.
* Facturas rectificativas.
* Facturas resumen de tiques.
* Permite imprimir el libro de IVA, basado en la misma legislación.

Instalación
===========

Este módulo depende del módulo *account_chart_update*, que se encuentra
en https://github.com/OCA/account-financial-tools.

Si el plan contable de su compañía ya está creado cuando instale este módulo,
recuerde utilizar el asistente de actualización del plan disponible n
*Contabilidad > Configuración -> Cuentas -> Actualizar plan contable*.

Configuración
=============

Los impuestos incluidos en este modelo se indican en los códigos de impuestos
de las bases imponibles. Eso puede modificarse en
*Contabilidad > Configuración > Impuestos > Códigos de impuestos*

Siguiendo el procedimiento del apartado instalación, por defecto se marcan
todos los códigos necesarios.

Uso
===

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Pruebe en Runbot
   :target: https://runbot.odoo-community.org/runbot/189/8.0

Errores conocidos / Hoja de ruta
================================

* Utilizar el patrón definido por la AEAT para el número de declaración.
* Facturas bienes de inversión.
* Facturas intracomunitarias. Operaciones a las que hace referencia el artículo
  66 del RIVA.
* Asientos contables de resumen de tiques.
* Exportación de asientos resumen de facturas.

Gestión de errores
==================

Los errores/fallos se gestionan en `las incidencias de GitHub <https://github.com/OCA/
l10n-spain/issues>`_.
En caso de problemas, compruebe por favor si su incidencia ha sido ya
reportada. Si fue el primero en descubrirla, ayúdenos a solucionarla proveyendo
una detallada y bienvenida retroalimentación
`aquí <https://github.com/OCA/
l10n-spain/issues/new?body=m%f3dulo:%20
l10n_es_aeat_mod340%0Aversi%f3n:%20
8.0%0A%0A**Pasos%20para%20reproducirlo**%0A-%20...%0A%0A**Comportamiento%20actual**%0A%0A**Comportamiento%20esperado**>`_.

Créditos
========

Contribuidores
--------------

* Ignacio Ibeas Izquierdo <ignacio@acysos.com>
* Ting
* NaN Projectes de Programari Lliure, S.L.
* OpenMind Systems
* Pedro M. Baeza <pedro.baeza@tecnativa.com>

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
