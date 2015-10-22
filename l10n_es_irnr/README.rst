.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

================================
Retenciones IRNR (No residentes)
================================

IRNR: Impuesto sobre la Renta de no Residentes sin establecimiento permanente.
Añade los impuestos, códigos de impuestos y posiciones fiscales para permitir
realizar la retención IRPF de no residentes.

La legislación vigente (2015) nos obliga a realizar las siguientes retenciones:

* Hasta el 31/12/2006 : 25% -> No es necesario por estar obsoleto
* Del 2007 al 2011: 24% -> No es necesario por estar obsoleto
* Del 2012 al 2014: 24,75% -> Necesario para migraciones, aplicable a todos los no residentes
* 2015 (Hasta 11/07/2015): 20% UE, 24% no-UE
* 2015 (Desde 12/07/2015): 19,50% UE, 24% no-UE
* 2016: 19% UE, 24% no-UE

Referencias
-----------

* `AEAT - Rentas obtenidas sin establecimiento permanente. Tipos de gravamen <http://www.agenciatributaria.es/AEAT.internet/Inicio/La_Agencia_Tributaria/Campanas/No_residentes/Impuesto_sobre_la_Renta_de_No_Residentes/No_residentes_sin_establecimiento_permanente/Cuestiones_basicas_sobre_tributacion/Rentas_obtenidas_sin_establecimiento_permanente__Tipos_de_gravamen.shtml>_`


Configuración
=============

Este addon añade los impuestos, códigos de impuestos y posiciones fiscales a
las siguientes plantillas:

* PGCE entidades sin ánimo de lucro 2008
* PGCE PYMEs 2008
* PGCE completo 2008

Para aplicar los cambios al plan contable que tengamos configurado en nuestra
compañía es posible que sea necesario instalar el addon
'OCA/account-financial-tools/account_chart_update' y actualizar:

* Impuestos
* Códigos de impuestos
* Posiciones fiscales


Uso
===

Las posiciones fiscales que nos añade este addon nos permiten:

* Como empresa que recibe una factura de un autónomo no residente:

Asignar al autónomo la posición fiscal por ejemplo
'Retención IRPF No residentes UE 20%'. Por lo tanto, al crear una factura de
proveedor de ese autónomo se aplicará la retencion del 20% a todas las líneas
de la factura.

* Como autónomo no residente que emite una factura a todos sus clientes

Asignar a todos los clientes que tienen una posición fiscal 'Régimen Nacional'
la posición fiscal 'Retención IRPF No residentes UE 20%'. Por lo tanto,
al crear una factura a un cliente se aplique la retención del 20% a todas
las líneas de la factura.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Pruébalo en Runbot
   :target: https://runbot.odoo-community.org/runbot/189/8.0


Créditos
========

Contribuidores
--------------

* Rafael Blasco <rafabn@antiun.com>
* Antonio Espinosa <antonioea@antiun.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
