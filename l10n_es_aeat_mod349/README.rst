.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=====================
Modelo 349 de la AEAT
=====================

Módulo para la presentación del Modelo AEAT 349 (Declaración Recapitulativa de
Operaciones Intracomunitarias)

Basado en la Orden EHA/769/2010 por el que se aprueban los diseños físicos y
lógicos del 349.

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

Instalación
===========
Para instalar este módulo es necesario instalar previamente el módulo
'account_invoice_refund_link', disponible en:
https://github.com/OCA/account-invoicing


Uso
===

Ir a:

* Contabilidad / Informes AEAT / Modelo 349
* Crear un nuevo registro e informar los datos básicos de la declaración.
* Pulsar 'Calcular' y revisar el resultado. Pulsar el botón 'Imprimir' para
  obtener el resultado en PDF.
* Para excluir ciertas operaciones de la declaración, ir a las pestañas
  'Registros de empresas' o 'Rectificaciones', y eliminar, en la seccion
  'Detalles', las operaciones que se desee excluir de la declaración.

Consideraciones importantes:
* En caso de indicar el tipo de declaración 'Suplementaria' o 'Normal' se
  propondrán todas las operaciones que apliquen para el periodo.
* En caso de indicar 'Complementaria', se propondrán únicamente aquellas
  operaciones que no hubieran sido aún presentadas en otra declaración.


.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/189/9.0


Créditos
========

Contribudores
-------------

* Luis Manuel Angueira Blanco (Pexego)
* Omar Castiñeira Saavedra<omar@pexego.es>
* Miguel López (Top Consultant)
* Ignacio Martínez (Top Consultant)
* Tecnativa (https://www.tecnativa.com):
  * Pedro M. Baeza <pedro.baeza@tecnativa.com>
  * Angel Moya <odoo@tecnativa.com>
  * Luis M. Ontalba <luis.martinez@tecnativa.com>
* Eficent (http://www.eficent.com)
  * Jordi Ballester <jordi.ballester@eficent.com>

Mantenedor
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
