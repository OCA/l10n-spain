# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com)
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2013 Joaquin Gutierrez (http://www.gutierrezweb.es)
#    Copyright (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Informes financieros para España",
    'version': "1.0",
    'author': "Spanish Localization Team,"
              "Zikzakmedia SL,"
              "J. Gutierrez,"
              "Serv. Tecnol. Avanzados - Pedro M. Baeza,"
              "Odoo Community Association (OCA)",
    'website': "http://odoospain.org",
    'category': "Localisation/Accounting",
    'description': """
.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License

Informes financieros de la localización española
================================================

Agrega el siguiente informe y la pantalla de parametrización del mismo:

* Libro diario.

Uso
===

El informe se puede encontrar dentro de *Contabilidad > Informes legales >
Informes contables > Libro diario*.

Problemas conocidos
===================

* El espaciado entre cada línea del asiento se ha tenido que establecer fijo,
  ya que si no salía muy grande de manera automática, por lo que habrá algún
  solape si la descripción de la línea es muy larga, sobretodo en la
  disposición vertical.

Créditos
========

Contribuidores
--------------

* Jordi Esteve <jesteve@zikzakmedia.com>
* Joaquin Gutierrez <joaquingpedrosa@gmail.com>
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

    """,
    'license': "AGPL-3",
    'depends': [
        "account",
        "l10n_es"
    ],
    'data': [
        "wizard/wizard_print_journal_entries_view.xml",
        "report/l10n_es_reports.xml",
    ],
    "installable": True,
}
