# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Spanish Localization Team
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com)
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2013 Acysos S.L. (http://acysos.com)
#                       Ignacio Ibeas <ignacio@acysos.com>
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
#    Copyright (c) 2015 Incaser (http://www.incaser.es)
#                       Sergio Teruel <sergio@incaser.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
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
    "name": "Adaptación de los clientes, proveedores y bancos para España",
    "version": "1.3",
    "author": "Spanish localization team",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Localisation/Europe",
    "license": "AGPL-3",
    "depends": [
        "base",
        "base_iban",
        "base_vat",
        "l10n_es_toponyms",
    ],
    "data": [
        "views/l10n_es_partner_view.xml",
        "wizard/l10n_es_partner_wizard.xml",
    ],
    "test": [
        "test/l10n_es_partner.yml",
    ],
    "installable": True,
}
