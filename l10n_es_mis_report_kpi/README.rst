.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=====================================================
Plantillas MIS Builder para análisis contable español
=====================================================

Incluye las siguientes plantillas para el motor de informes provisto
por el módulo *mis_builder*:

    * Ratios de Balance PYMEs (PGCE 2008)
    * Ratios Cuenta de pérdidas y ganancias PYMEs (PGCE 2008)
    * Ratios de Balance abreviado (PGCE 2008)
    * Ratios de Cuenta de pérdidas y ganancias abreviado (PGCE 2008)
    * Ratios Balance normal (PGCE 2008)
    * Ratios de Cuenta de pérdidas y ganancias completo (PGCE 2008)

Instalación
===========
Este módulo depende del módulo 'mis_builder' que puede obtenerse
en https://apps.odoo.com, o bien en https://github.com/OCA/mis-builder.

Uso
===

#. Acceda a *Contabilidad > Informes > MIS > Informes MIS*
#. Cree un nuevo informe,
#. Seleccione una de las plantillas que se corresponde con los informes
   financieros españoles.
#. Desmarque la opción de evitar auto-expansión de cuentas si desea que
   se oculten las cuentas contables y se muestren solamente los niveles
   predefinidos por el formato oficial.
#. Para seleccionar los periodos puede:

   * Seleccionar directamente el intervalo de fechas deseado o el nombre del
     rango para obtener el informe únicamente para ese periodo.
   * Pulsar sobre "Modo de comparación", e introducir en la pestaña "Columnas"
     tantas líneas como distintas periodos se quieran poner. Dichos periodos
     se pueden definir también con fechas fijas, o poner periodos relativos
     (por ejemplo "Tipo de periodo" = "Año", "Desplazamiento" = "0" y
     "Duración" = "1" para el año N, y lo mismo pero con "Desplazamiento" =
     "-1" para el año N - 1. No hay que olvidar que la fecha base del informe
     esté en el año a analizar).

#. Pulse sobre "Previsualizar", "Imprimir" o "Exportar" para calcular el
   informe y realizar la acción pulsada.
#. Si está en modo previsualización, podrá pulsar sobre la cifra de las
   filas detalle para ver los apuntes relacionados con dicha cifra.

*AVISO*: El informe solamente considera las cuentas numeradas de acuerdo con el
formato establecido por el PGCE. Cualquier cuenta personalizada que no sea
subcuenta (tenga la misma , deberá ser
añadida

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/119/11.0


Incidencias
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-spain/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and
welcomed feedback `here <https://github.com/OCA/l10n-spain/issues/new>`_.

Créditos
========

Contribuidores
--------------

* Jordi Ballester (EFICENT) <jordi.ballester@eficent.com>
* Aarón Henríquez (EFICENT) <ahenriquez@eficent.com>
* Albert Cabedo (GAFIC) <albert@gafic.com>
* Antonio Cánovas Pedreño (INGENIERÍA CLOUD) <antonio.canovas@ingenieriacloud.com>
* Antonio Cánovas Pedreño (INGENIERÍA CLOUD) <antonio.canovas@ingenieriacloud.com>


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
