.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=====================
Importaciones con DUA
=====================

Este addon pretende ayudar con la contabilidad de facturas de importación
cuando una empresa de tránsito de aduanas realiza una valoración de mercancía
cambiando la valoración inicial del proveedor extranjero y aplicando el IVA
correspondiente en una factura separada.


Configuración
=============

Este addon añade los impuestos y posiciones fiscales a las siguientes plantillas:

* PGCE entidades sin ánimo de lucro 2008
* PGCE PYMEs 2008
* PGCE completo 2008

Para aplicar los cambios al plan contable que tengamos configurado en nuestra
compañía es posible que sea necesario instalar el addon
'OCA/account-financial-tools/account_chart_update' y actualizar:

* Impuestos
* Posiciones fiscales

Una vez actualizado el plan contable (Impuestos y Posiciones fiscales) es
necesario asignar los impuestos a los productos DUA que crea este addon para
facilitar la contabilidad de las facturas de la empresa de tránsito:

1. Ir a Compras > Productos > Productos
2. Quitar el filtro por defecto y buscar "DUA"
3. Asignar los siguientes impuestos en el campo "Impuestos proveedor"
    * DUA Compensación: "DUA Exento"
    * DUA Valoración IVA 10%: "IVA 10% Importaciones bienes corrientes"
    * DUA Valoración IVA 21%: "IVA 21% Importaciones bienes corrientes"
    * DUA Valoración IVA 4%: "IVA 4% Importaciones bienes corrientes"


Uso
===

Este addon crea los siguientes objetos contables:

* Impuesto: DUA Exento

Este nuevo impuesto es un impuesto "inocuo" que es equivalente a no poner
ningún impuesto. Sirve para cumplir con el requisitos de definir al menos un
impuesto por cada línea en la factura (si está instalado el addon
OCA/account-financial-tools/account_invoice_tax_required).

* Posicion fiscal: Importación con DUA

Esta posición fiscal cambia los impuestos de compras por el impuesto
"DUA Exento" para que las líneas de la factura de proveedor no generen
información de impuestos

Además, crea los siguientes productos para facilitar la creación de la
factura emitida por la empresa de tránsito:

* Producto: DUA Valoración xx %

Productos para indicar la nueva valoración de la mercancía importada realizada
por la empresa de tránsito. Esta valoración es la base imponible para calcular
el IVA a abonar.

* Producto: DUA Compensación

Producto para indicar la misma valoración pero con signo negativo para
compensar el apunte al debe que genera el producto "DUA Valoración xx %"
anterior

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/189/11.0


Procedimiento
=============

Ejemplo:

* Compramos una mercancía a un proveedor extranjero por valor de 100,00 €
* La aduana valora la mercancía en 150,00 €
* La empresa de tránsito nos factura el IVA: 31,50 € (21% de 150,00 €)
* Al proveedor extranjero le debemos 100,00 €
* A la empresa de tránsito le debemos 31,50 €
* La base imponible (casilla 32 del modelo 303) es 150,00 €
* La cuota a deducir (casilla 33 del modelo 303) es 31,50 €

1. Factura proveedor extranjero

   * Esta factura nos indica la mercancía comprada (100,00 €) y no lleva IVA.
   * Creamos la factura con la posición fiscal "Importación con DUA".
   * Añadimos los productos comprados y el impuesto en cada línea será "DUA Exento"

2. Factura empresa de tránsito

   * Esta factura nos indica el IVA a pagar para retirar la mercancía de aduanas.
   * Creamos la factura con la posición fiscal "Importación con DUA"
   * Añadimos una línea con el producto "DUA Valoración 21 %" con precio 150,00 €
     El impuesto en esa línea será "IVA 21% Importaciones bienes corrientes"
   * Añadimos otra línea con el producto "DUA Compensación" con precio -150,00 €
     El impuesto en esa línea será "DUA Exento"

Al validar ambas facturas nos crea los siguientes asientos:

1. Asiento factura proveedor extranjero

    .. csv-table::
       :header: "CUENTA", "DEBE", "HABER", "IMPUESTO", "IMPORTE IMPUESTO"
       :widths: 30, 10, 10, 30, 10

       "400000 Proveedores", 0.00, 100.00
       "600000 Compras", 100.00, 0.00

2. Asiento factura empresa de tránsito

    .. csv-table::
       :header: "CUENTA", "DEBE", "HABER", "IMPUESTO", "IMPORTE IMPUESTO"
       :widths: 30, 10, 10, 30, 10

       "410000 Acreedores", 0.00, 31.50
       "472000 IVA Soportado", 31.50, 0.00, "Importaciones. Cuota 21%", 31.50
       "600000 Compras", 0.00, 150.00
       "600000 Compras", 150.00, 0.00, "Importaciones. Base 21%", 150.00


Créditos
========

Contribuidores
--------------

* Rafael Blasco <rafabn@antiun.com>
* Antonio Espinosa <antonioea@antiun.com>
* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
* Albert Cabedo <albert@gafic.com>
* Luis M. Ontalba <luis.martinez@tecnativa.com>

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
