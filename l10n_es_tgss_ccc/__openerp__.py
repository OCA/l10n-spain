# -*- encoding: utf-8 -*-

# Odoo, Open Source Management Solution
# Copyright (C) 2014-2015  Grupo ESOC <www.grupoesoc.es>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

{
    "name": "Código de Cuenta de Cotización",
    "version": "1.0",
    "category": "Project",
    "author": "Odoo Community Association (OCA), Grupo ESOC",
    "license": "AGPL-3",
    "website": "https://odoospain.odoo.com/",
    "installable": True,
    "application": False,
    "summary": "Añadir CCC/NAF de la TGSS a los contactos",
    "depends": [
        "hr",
    ],
    "data": [
        "views/res_partner.xml",
        "views/hr_employee.xml",
    ],
}
