# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    $Id$
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
    "name" : "Instalación PYME estándar sólo contabilidad",
    "version" : "1.0",
    "author" : "Zikzakmedia SL",
    "category" : "Generic Modules/Others",
    "website": "www.zikzakmedia.com",
    "description": """Instalación de los módulos contables de OpenERP para una PYME estándar incluyendo los módulos de localización española y algunos datos de configuración iniciales.

Instala los módulos habituales para la gestión contable de una PYME del Estado Español: contabilidad y facturación, pagos, remesas de recibos, plan contable 2008, topónimos, datos de bancos españoles y su validación, importación de extractos bancarios, cierre de ejercicio, informes contables, ...

Cuando se ejecute el asistente de configuración de contabilidad (account) deberá omitir el paso, pués la selección del plan contable y la creación de ejercicios y períodos fiscales lo realiza este módulo de forma automática.

Después de instalar este módulo y todas sus dependencias, deberá crear los topónimos del Estado Español (crear las provincias mediante el asistente que se ejecuta automáticamente) y las cuentas contables a partir de la plantilla (mediante el menú "Gestión financiera/Configuración/Contabilidad financiera/Plantillas/Generar plan contable a partir de una plantilla de plan contable").

Posteriormente podrá crear los bancos españoles mediante el menú "Empresas/Configuración/Bancos/Asistente de importación de todos los bancos del Estado Español" y los conceptos de extractos bancarios mediante el menú "Gestión financiera/Configuración/Extractos bancarios C43/Asistente de importación de conceptos de extractos".
""",
    "license" : "GPL-3",
    "depends" : ["base", "account", "account_payment", "account_payment_extension", "account_renumber", "account_financial_report", "l10n_es", "l10n_es_toponyms", "l10n_es_partner", "l10n_es_partner_seq", "l10n_es_payment_extension", "l10n_es_bank_statement", "l10n_es_fiscal_year_closing", "l10n_es_account_balance_report", "l10n_es_aeat_mod347"],
    "init_xml" : ["pyme_data.xml"],
    "demo_xml" : [],
    "update_xml" : [
    ],
    "active": False,
    "installable": True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
