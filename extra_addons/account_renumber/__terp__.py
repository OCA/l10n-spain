# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP - Account renumber wizard
#    Copyright (C) 2009 Pexego Sistemas Informáticos. All Rights Reserved
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
        "name" : "Account renumber wizard",
        "version" : "0.1",
        "author" : "Pexego",
        "website" : "http://www.pexego.es",
        "category" : "Enterprise Specific Modules",
        "description": """
The module allows the user to renumber accounting entries by date.

Renumbering can be done per journal, and between dates. It will
recreate the sequence number of each account move, so the moves
have a sequence number ascending by date.
            """,
        "depends" : [
                'base',
                'account',
            ],
        "init_xml" : [
            ],
        "demo_xml" : [ ],
        "update_xml" : [
                'account_renumber_wizard.xml',
            ],
        "installable": True
}
