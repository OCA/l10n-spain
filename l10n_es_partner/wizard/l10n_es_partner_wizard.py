# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2013 Servicios Tecnológicos Avanzados (http://www.serviciosbaeza.com)
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
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
from osv import orm, fields
import tools
import os

class l10n_es_partner_import_wizard(orm.TransientModel):
    _name = 'l10n.es.partner.import.wizard'
    _inherit = 'res.config.installer'

    def execute(self, cr, uid, ids, context=None):
        if context is None: context = {}
        super(l10n_es_partner_import_wizard, self).execute(cr, uid, ids, context=context)
        try:
            fp = tools.file_open(os.path.join(os.path.join('l10n_es_partner', 'wizard'), 'data_banks.xml'))
        except IOError, e:
            return {}
        idref = {}
        tools.convert_xml_import(cr, 'l10n_es_partner', fp,  idref, 'init', noupdate=True)
        fp.close()
        return {}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
