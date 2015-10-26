# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2014 Domatix Technologies  S.L. (http://www.domatix.com)
#                       info <info@domatix.com>
#                        Angel Moya <angel.moya@domatix.com>
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
    "name": "Certificado de subcontratista",
    "version": "8.0.1.0.0",
    "author": "Domatix,Odoo Community Association (OCA)",
    "website": "www.domatix.com",
    "category": "Accounting",
    "depends": ["purchase"],
    "data": ["views/subcontractor_certificate_view.xml"],
    "demo": [],
    "auto_install": False,
    "installable": True,
}
