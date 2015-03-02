# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#                       Jesús Martín <jmartin@zikzakmedia.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name" : "Instalación PYME estándar sólo contabilidad",
    "version" : "1.0",
    "author" : "Zikzakmedia SL,Odoo Community Association (OCA)",
    "category" : "Generic Modules/Others",
    "website": "www.zikzakmedia.com",
    "description": """
Instalación de los módulos contables de OpenERP para una PYME estándar incluyendo los módulos de localización española y algunos datos de configuración iniciales.

Instala los módulos habituales para la gestión contable de una PYME del Estado Español: contabilidad y facturación, pagos, remesas de recibos, plan contable 2008, topónimos, datos de bancos españoles y su validación, importación de extractos bancarios, cierre de ejercicio, informes contables, ...

Cuando se ejecute el asistente de configuración de contabilidad (account) deberá omitir el paso, pués la selección del plan contable y la creación de ejercicios y períodos fiscales lo realiza este módulo de forma automática.

Después de instalar este módulo y todas sus dependencias, deberá crear los topónimos del Estado Español (crear las provincias mediante el asistente que se ejecuta automáticamente) y las cuentas contables a partir de la plantilla de plan contable (con el asistente que se ejecuta automáticamente o mediante el menú "Contabilidad/Configuración/Contabilidad financiera/Configuración financiera para nueva compañía").

Posteriormente podrá crear los bancos españoles mediante el menú "Ventas/Configuración/Libreta de direcciones/Bancos/Asistente de importación de todos los bancos del Estado Español" y los conceptos de extractos bancarios mediante el menú "Contabilidad/Configuración/Varios/Extractos bancarios C43/Asistente de importación de conceptos de extractos".
""",
    "license" : "AGPL-3",
    "depends" : [
        "account",
        "account_financial_report",
        "account_payment",
        "account_payment_extension",
        "account_renumber",
        "l10n_es",
        "l10n_es_account",
        "l10n_es_account_balance_report",
        "l10n_es_aeat",
        "l10n_es_aeat_mod340",
        "l10n_es_aeat_mod347",
        "l10n_es_aeat_mod349",
        "l10n_es_bank_statement",
        "l10n_es_fiscal_year_closing",
        "l10n_es_partner",
        "l10n_es_partner_seq",
        "l10n_es_payment_order",
        "l10n_es_toponyms",
    ],
    "init_xml" : [
        "pyme_data.xml",
    ],
    "demo_xml" : [],
    "update_xml" : [
        'account_installer.xml',
    ],
    "active": False,
    "installable": False
}

