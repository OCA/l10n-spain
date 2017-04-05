Modelo 349 de la AEAT
=====================

Módulo para la presentación del Modelo AEAT 349 (Declaración Recapitulativa de
Operaciones Intracomunitarias)

Basado en la Orden EHA/769/2010 por el que se aprueban los diseños físicos y
lógicos del 349.

Según el Artículo 76 de la Ley del IVA,
En las adquisiciones intracomunitarias de bienes, el impuesto se devengará en
el momento en que se consideren efectuadas las entregas de bienes similares de
conformidad con lo dispuesto en el artículo 75 de esta Ley.

No se deben de tener en cuenta las facturas de anticipo en el modelo 349.

Para ello se ha creado un checkbox en las cuentas, para marcar aquellas que no
se deben de incluir en el modelo 349 y en los cálculos de los importes y el
detalle de registros a incluir en el modelo, se tiene en cuenta que no
pertenezcan a las cuentas marcadas y se calcula el total a partir del
sumatorio de las bases de tax_line, para poder efectuar el filtrado de las
cuentas.

Por defecto se marcan como no incluibles las cuentas hijas de la 438 (Anticipos
de Clientes) y las cuentas hijas de la 407 (Anticipos de proveedores).


De acuerdo con la normativa de la Hacienda Española, están obligados a
presentar el modelo 349:

 * Todos aquellos sujetos pasivos del Impuesto sobre el Valor Añadido que hayan
   realizado las operaciones previstas en el artículo 79 del Reglamento del
   Impuesto sobre el Valor Añadido, es decir, quienes adquieran o vendan bienes
   a empresas situadas en países miembros de la UE, sino también aquellos que
   presten servicios a miembros de la UE y cumplan con las siguientes
   condiciones:

  - Que conforme a las reglas de la localización aplicables a las
    mismas, no se entiendan prestadas en el territorio de aplicación del
    impuesto.

  - Que estén sometidas efectivamente a gravamen de otro Estado miembro.

  - Que su destinatario sea un empresario o profesional actuando como
    tal y radique en dicho Estado miembro la sede de su actividad
    económica, o tenga en el mismo un establecimiento permanente o, en su
    defecto, el lugar de su domicilio o residencia habitual, o que dicho
    destinatario sea una persona jurídica que no actúe como empresario o
    profesional pero tenga asignado un número de identificación a efectos
    del Impuesto suministrado por ese Estado miembro.

  - Que el sujeto pasivo sea dicho destinatario.

    El período de declaración comprenderá, con carácter general las
    operaciones realizadas en cada mes natural, y se presentará durante los
    veinte primeros días naturales del mes inmediato siguiente al
    correspondiente período mensual. No obstante, la presentación podrá ser
    bimestral, trimestral o anual en los siguientes supuestos:

 * Bimestral: Si al final del segundo mes de un trimestre natural el
   importe total de las entregas de bienes y prestaciones de servicios que
   deban consignarse en la declaración recapitulativa supera 100.000 euros
   (a partir de 2012, el umbral se fija en 50.000 euros).

 * Trimestral: Cuando ni durante el trimestre de referencia ni en cada uno
   de los cuatro trimestres naturales anteriores el importe total de las
   entregas de bienes y prestaciones de servicios que deban consignarse en la
   declaración recapitulativa sea superior a 100.000 euros.

 * Anual: En los treinta primeros días de enero del año siguiente ( la
   primera sería en enero de 2011) si el importe total de las entregas de
   bienes o prestaciones de servicios  del año ( excluido IVA), no supera los
   35.000 € y el importe total de las entregas de bienes a otro Estado
   Miembro (salvo medios de transporte nuevos) exentas de IVA no sea superior
   a 15.000 €.

Installation
============

Para instalar este módulo, es necesario instalar el módulo
*account_invoice_currency*, que se encuentra en el repositorio de GitHub:

https://github.com/OCA/account-financial-tools

Credits
=======

Contributors
------------
* Luis Manuel Angueira Blanco (Pexego)
* Omar Castiñeira Saavedra<omar@pexego.es>
* Miguel López (Top Consultant)
* Ignacio Martínez (Top Consultant)
* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
* Antonio Espinosa <antonioea@antiun.com>

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
