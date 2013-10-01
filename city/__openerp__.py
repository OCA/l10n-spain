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
    "name" : "City information",
    "version" : "2.1",
    "author" : "Acysos S.L., Pedro Manuel Baeza, Pablo Rocandio",
    "website" : "www.acysos.com, www.serviciosbaeza.com",
    "license" : "AGPL-3",
    "category" : "Hidden",
    "description": """
    Helps to keep homogeneous address data in the Database
    ------------------------------------------------------
    Creates a model for storing cities and all their information.
    
    Zip code, city, state and country fields can be filled automatically when
    a location field is completed.
    """,
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
