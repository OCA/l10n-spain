.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License

IGIC (Impuesto General Indirecto Canario)
=========================================

* Define plantillas de impuestos IGIC.
* Define plantillas de códigos de impuestos IGIC.
* Define plantillas de cuentas contables IGIC.

En funcionamiento pero faltan cosas por pulir:

- Repensar las abreviaturas de los impuestos igic.
- i18n : traducciones
- test

Instalación
===========

Al instalar el módulo se crean las plantillas de códigos de impuestos,
impuestos y cuentas contables relacionadas con el igic.
Cuando se cree el plan contable para una compañía se crearán los códigos,
impuestos y cuentas del igic correspondientes.

Si el plan contable ya estaba instalado, para añadir los impuestos igic
se ha de hacer mediante el módulo account_chart_update, con el detalle de
que las cuentas contables han de crearse manualmente.


Créditos
========

* David Diz Martínez <daviddiz@gmail.com>

