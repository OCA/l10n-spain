# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015-TODAY MINORISA (http://www.minorisa.net) All Rights Reserved.
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

from openerp import api, models, fields, _
from openerp.exceptions import ValidationError


class AeatSiiMappingRegistrationKeys(models.Model):
    _name='aeat.sii.mapping.registration.keys'
    _description = 'Aeat SII Invoice Registration Keys'
    
    
    #registration_id = fields.Many2one('aeat.sii.invoice.registration','Aeat SII Invoice Registration')
    code = fields.Char('Code',required=True,size=2)
    name = fields.Char('Name',required=True)
    #type = fields.Selection([('sale','Sale'),('purchase','Purchase'),('all','All')],'Type',required=True)
    type = fields.Selection([('sale','Sale'),('purchase','Purchase')],'Type',required=True)
    
    @api.multi
    def name_get(self):
        vals = []
        for record in self:
            name=u''
            name += "[%s]" % record.code
            name+= "-%s"%record.name
            vals.append(tuple([record.id, name]))
        return vals