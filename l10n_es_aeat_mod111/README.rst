.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

================================
Presentación del Modelo AEAT 111
================================

Modelo 111 de la AEAT. Retenciones e ingresos a cuenta. Rendimientos del
trabajo y de actividades económicas, premios y determinadas ganancias
patrimoniales e imputaciones de Renta. Autoliquidación.

Uso
===

Para crear un modelo, por ejemplo de un trimestre del año:

1. Ir a Contabilidad > Informe > Informes legales > Declaraciones AEAT > Modelo 111
2. Pulsar en el botón "Crear"
3. Seleccionar el ejercicio fiscal y el tipo de período, los periodos incluidos
   se calculan automáticamente
4. Seleccionar el tipo de declaración
5. Rellenar el teléfono y teléfono móvil, necesarios para la exportacion BOE
6. Guardar y pulsar en el botón "Calcular"
7. Rellenar (si es necesario) aquellos campos que Odoo no calcula automáticamente:

   * Rendimientos del trabajo: Dinerarios ([01], [02], [03]) y en especie ([04], [05], [06])
   * Premios por la participación en juegos, concursos, ...: Dinerarios ([13], [14], [15]) y en especie ([16], [17], [18])
   * Ganancias patrimoniales derivadas de los aprovechamientos forestales ...: Dinerarias ([19], [20], [21]) y en especie ([22], [23], [24])
   * Contraprestaciones por la cesión de derechos de imagen ...: Casillas [25], [26] y [27]
   * Resultados a ingresar anteriores: Casilla [29]

8. Cuando los valores sean los correctos, pulsar en el botón "Confirmar"
9. Podemos exportar en formato BOE para presentarlo telemáticamente en el portal
   de la AEAT

NOTA: En el caso en que tengamos el addon 'l10n_es_aeat_mod216' deberemos
indicar los proveedores que son residentes (éste es el valor por defecto),
en la ficha de la empresa: Contabilidad > Proveedores > Proveedores, pestaña de
Contabilidad. El campo "Es no residente" no debe estar marcado para que
las retenciones realizadas a éste proveedor se incluyan en el modelo 111

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Pruébalo en Runbot
   :target: https://runbot.odoo-community.org/runbot/189/10.0


Créditos
========

Contribuidores
--------------

* MálagaTIC (http://www.malagatic.com)
* Carlos Sánchez Cifuentes <csanchez@grupovermon.com>
* Pedro M. Baeza <pedro.baeza@tecnativa.com>
* AvanzOSC (http://www.avanzosc.es)
* Antonio Espinosa <antonio.espinosa@tecnativa.com>
* RGB Consulting SL (http://www.rgbconsulting.com)
* Vicent Cubells (http://obertix.net)
* Jose Maria Alzaga (http://www.aselcis.com)
* Ismael Calvo (http://factorlibre.com)

Financiadores
-------------
La migración de este módulo forma parte de una campaña de migración de la
localización española que ha sido posible gracias a la colaboración económica
de las siguientes empresas (por orden alfabético):

* `Aizean evolution <http://www.aizean.com>`_
* `Aselcis consulting <https://www.aselcis.com>`_
* `AvanzOSC <http://avanzosc.es>`_
* `Diagram software <http://diagram.es>`_
* `Domatix <http://www.domatix.com>`_
* `Eficent <http://www.eficent.com>`_
* `FactorLibre <http://factorlibre.com>`_
* `Fairhall solutions <http://www.fairhall.es>`_
* `GAFIC SLP <http://www.gafic.com>`_
* `Incaser <http://www.incaser.es>`_
* `Ingeos <http://www.ingeos.es>`_
* `Nubistalia <http://www.nubistalia.es>`_
* `Punt sistemes <http://www.puntsistemes.es>`_
* `Praxya <http://praxya.com>`_
* `Reeng <http://www.reng.es>`_
* `Soluntec <http://www.soluntec.es>`_
* `Tecnativa <https://www.tecnativa.com>`_
* `Trey <https://www.trey.es>`_
* `Vicent Cubells <http://vcubells.net>`_

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
