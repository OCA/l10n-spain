###############################################################################
#
#    SDi Digital Group
#    Copyright (C) 2021-Today SDi Digital Group <www.sdi.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    "name": "Delivery ViaXpress",
    "summary": "Delivery Carrier implementation for ViaXpress",
    "version": "17.0.1.0.0",
    "category": "Stock",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "SDi, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "images": ["static/description/banner.png"],
    "application": False,
    "installable": True,
    "depends": [
        "delivery_package_number",
        "delivery_state",
        "stock",
    ],
    "external_dependencies": {
        "python": ["suds"],
    },
    "data": [
        "views/res_company_view.xml",
        "views/stock_picking_views.xml",
    ],
    "maintainers": [
        "idelapoza",
    ],
}
