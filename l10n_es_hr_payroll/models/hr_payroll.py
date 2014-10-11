# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2014 Joaquin Gutierrez Pedrosa All Rights Reserved.
#    Copyright (c) 2014 Pedro Manuel Baeza Romero All Rights Reserved.
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
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


from openerp.osv import orm
from openerp.osv import fields
from openerp.tools.translate import _


class HrContract(orm.Model):
    _inherit = "hr.contract"
    _description = 'Employee Contract'

    _columns = {
        'insurance_company': fields.float('Company Insurance',
                                          digits=(16, 2),
                                          required=True,
                                          help="Company Insurance"),
        'insurance_employee': fields.float('Employee Insurance',
                                           digits=(16, 2),
                                           required=True,
                                           help="Employee Insurance"),
        'retention_employee': fields.float('Employee Retention',
                                           digits=(16, 2),
                                           required=True,
                                           help="Employee Retentions"),
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
