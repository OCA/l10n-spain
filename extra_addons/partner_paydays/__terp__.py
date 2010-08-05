##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 NaN Projectes de Programari Lliure, S.L.  All Rights Reserved
#                       http://www.NaN-tic.com
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
    'name' : 'Partner Paydays',
    'version' : '1.0',
    'description' : "This module adds fields to introduce partner's paydays & holidays. It also allows due date in customer invoices to take into account vacations if the partner doesn't pay during that period.",
    "author" : "Nan, \n contributor readylan",
    'website' : 'http://www.NaN-tic.com',
    'depends' : [
        'base','account'
    ],
    'category' : 'Custom Modules',
    'init_xml' : [],
    'demo_xml' : [],
    'update_xml' : [
        'partner_paydays_view.xml',
        #todo: 'security/ir.model.access.csv',
    ],
    'active': False,
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
