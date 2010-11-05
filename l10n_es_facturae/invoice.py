# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Alejandro Sanchez (http://www.asr-oss.com) All Rights Reserved.
#                       Alejandro Sanchez <alejandro@asr-oss.com>
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

from osv import osv
import netsvc

class account_invoce(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'
    #demomento deshabilitado (graba cuando se genero)
    #_columns = {
    #    'date_done': fields.date('Execution date', readonly=True),
    #}
    def set_done(self, cr, uid, id, *args):
        #self.write(cr,uid,id,{'date_done': time.strftime('%Y-%m-%d'),'state': 'done',})
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'account.invoce', id, 'done', cr)
        return True

account_invoce()


