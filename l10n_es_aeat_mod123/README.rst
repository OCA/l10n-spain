.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

================================
Presentación del Modelo AEAT 123
================================

Modelo 123 de la AEAT. Retenciones e ingresos a cuenta del Impuesto sobre la
Renta de las Personas Físicas, Impuesto sobre Sociedades y del Impuesto sobre
la Renta de no Residentes (establecimientos permanentes). Determinados
rendimientos del capital mobiliario o determinadas rentas.

Este modelo tiene su utilidad sobre todo en préstamos entre empresas o
particulares, o financiaciones recibidas por ENISA (Empresa Nacional de
Innovación) o CDTI (Centro para el Desarrollo Tecnológico Industrial).

Otra utilidad que se le da es para las retenciones en los repartos de
dividendos.

El modelo se presentará mensualmente para grandes empresas, y mensualmente
para el resto, por parte de aquellas empresas que deban abonar intereses de
esos préstamos.

Instalación
===========

Este módulo depende del módulo _l10n_es_ que está en este mismo repositorio
(pero que debe tener más prioridad que el de Odoo base), con la versión mínima
5.4. Para que el módulo funcione, el plan de cuentas debe estar actualizado.
Utilice _account_chart_update_ para ello.

Uso
===

Para introducir datos válidos para el modelo:

#. Realizar una factura de proveedor de los intereses cobrados por la empresa
   o particular prestatario con impuesto "Retenciones 21% (préstamos)".
#. O también puede realizar una factura de proveedor del reparto de dividendos
   con el impuesto "Retenciones 19% (dividendos)".
#. Validarla.

Para crear una declaración del modelo:

#. Ir a Contabilidad > Informe > Informes legales > Declaraciones AEAT >
   Modelo 123.
#. Pulsar en el botón "Crear".
#. Seleccionar el ejercicio fiscal y el tipo de período. Los periodos incluidos
   se calculan automáticamente.
#. Seleccionar el tipo de declaración.
#. Rellenar el teléfono, necesario para la exportacion BOE.
#. Guardar y pulsar en el botón "Calcular".
#. Cuando revise los valores, pulse en el botón "Confirmar".
#. Se puede exportar la declaración en formato BOE para presentarla
   telemáticamente en el portal de la AEAT

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Pruébalo en Runbot
   :target: https://runbot.odoo-community.org/runbot/189/8.0


Créditos
========

Contribuidores
--------------

* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>

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
