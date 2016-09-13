.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

======================================
Cierre de ejercicio fiscal para España
======================================

Reemplaza el asistente por defecto de OpenERP para el cierre contable (del
módulo *account*) por un asistente todo en uno más avanzado que permite:

 * Comprobar asientos descuadrados.
 * Comprobar fechas y periodos incorrectos de los apuntes.
 * Comprobar si hay asientos sin asentar en el ejercicio a cerrar.
 * Crear el asiento de pérdidas y ganancias.
 * Crear el asiento de pérdidas y ganancias de patrimonio neto.
 * Crear el asiento de cierre.
 * Crear el asiento de apertura.

Permite configurar todos los parámetros para la realización de los asientos,
aunque viene preconfigurado para el actual plan de cuentas español.

Uso
===

Para la creación de los asientos, se tiene en cuenta el método de cierre
definido en los tipos de cuenta (siempre que la cuenta no sea de tipo view):

 * Ninguno: No se realiza ningún cierre para esa cuenta.
 * Saldo: Crea un apunte para la cuenta con el saldo del ejercicio.
 * No conciliados: Crea un apunte por cada empresa con saldo para la cuenta.
 * Detalle: No soportado.

También conserva el estado del cierre, por lo que el usuario puede cancelar y
deshacer las operaciones fácilmente.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/189/9.0


Gestión de errores
==================

Los errores/fallos se gestionan en `las incidencias de GitHub <https://github.com/OCA/
l10n-spain/issues>`_.
En caso de problemas, compruebe por favor si su incidencia ha sido ya
reportada. Si fue el primero en descubrirla, ayúdenos a solucionarla indicando
una detallada descripción
`aquí <https://github.com/OCA/
l10n-spain/issues/new?body=m%f3dulo:%20
l10_es_fiscal_year_closing%0Aversi%f3n:%20
9.0%0A%0A**Pasos%20para%20reproducirlo**%0A-%20...%0A%0A**Comportamiento%20actual**%0A%0A**Comportamiento%20esperado**>`_.

Créditos
========

Contribuidores
--------------

* Jordi Esteve <jesteve@zikzakmedia.com>
* Pedro Tarrafeta <pedro@acysos.com>
* Avanzosc (http://www.avanzosc.com)
* Joaquin Gutierrez (http://www.gutierrezweb.es)
* Pedro M. Baeza <pedro.baeza@tecnativa.com>
* Antonio Espinosa <antonio.espinosa@tecnativa.com>

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
