#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
    "name" : "City-Helps to keep Homogeneous address data in the Database",
    "version" : "2.0",
    "author" : "Acysos S.L., Pedro Manuel Baeza, Pablo Rocandio",
    "website" : "www.acysos.com, www.serviciosbaeza.com",
    "license" : "AGPL-3",
    "category" : "Hidden",
    "description": """Creates a model for storing cities
Zip code, city, state and country fields are replaced with a location field in partner and partner contact forms.
This module helps to keep homogeneous address data in the database.""",
    "depends" : ["base"],
    "init_xml" : [],
    "update_xml" : [
        'city_view.xml',
        'partner_view.xml',
        'country_view.xml',
        'company_view.xml',
        'security/ir.model.access.csv'
        ],
    "active": False,
    "installable": True
}
