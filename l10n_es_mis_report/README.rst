.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

========================================================
Plantillas MIS Builder para informes contables españoles
========================================================

Incluye las siguientes plantillas para el motor de informes provisto
por el módulo *mis_builder*:

    * Balance PYMEs (PGCE 2008)
    * Cuenta de pérdidas y ganancias PYMEs (PGCE 2008)
    * Balance abreviado (PGCE 2008)
    * Cuenta de pérdidas y ganancias abreviado (PGCE 2008)
    * Balance normal (PGCE 2008)
    * Cuenta de pérdidas y ganancias completo (PGCE 2008)
    * Estado de ingresos y gastos reconocidos (PGCE 2008)

Las plantillas están basadas en los modelos para el depósito de cuentas anuales
del Registro Mercantil:

* *Normal*: http://www.mjusticia.gob.es/cs/Satellite/Portal/1292427306020
* *Abreviado*: http://www.mjusticia.gob.es/cs/Satellite/Portal/1292427306005
* *PYMEs*: http://www.mjusticia.gob.es/cs/Satellite/Portal/1292427306035


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
   :target: https://runbot.odoo-community.org/runbot/119/9.0


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
