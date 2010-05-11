# -*- encoding: utf-8 -*-
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
    "name" : "Instalación PYME estándar (1er paso)",
    "version" : "1.0",
    "author" : "Zikzakmedia SL",
    "category" : "Generic Modules/Others",
    "website": "www.zikzakmedia.com",
    "description": """Instalación OpenERP para una PYME estándar (1er paso).

Instala los módulos habituales de una PYME del Estado Español: ventas, compras, TPV, productos, stocks, contabilidad y facturación, pagos, remesas de recibos, plan contable 2008, topónimos.

Cuando se ejecute el asistente de configuración de contabilidad (account) deberá omitir el paso, pués la selección del plan contable y la creación de ejercicios y períodos fiscales lo realiza este módulo y l10_ES_pyme_custom de forma automática.

Después de instalar este módulo y todas sus dependencias, deberá crear los topónimos del Estado Español (crear las provincias mediante el asistente que se ejecuta automáticamente) y las cuentas contables a partir de la plantilla (mediante el menú Gestión financiera/Configuración/Contabilidad financiera/Plantillas/Generar plan contable a partir de una plantilla de plan contable).

Posteriormente, instalando el módulo l10_ES_pyme_custom, se instalaran los módulos restantes: l10n_ES_extractos_bancarios, l10n_ES_partner""",
    "license" : "GPL-3",
    "depends" : ["base", "account", "account_payment", "account_payment_extension", "account_renumber", "account_financial_report", "point_of_sale", "product", "sale", "sale_payment", "purchase", "stock", "label", "partner_spam", "l10n_ES_remesas", "l10n_chart_ES", "l10n_ES_toponyms", "l10n_ES_partner_data", "l10n_ES_partner_seq"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [],
    "active": False,
    "installable": True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
