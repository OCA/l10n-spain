# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009 Alejandro Sanchez (http://www.asr-oss.com) All Rights Reserved.
#                    Alejandro Sanchez <alejandro@asr-oss.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import osv,fields
import time
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


