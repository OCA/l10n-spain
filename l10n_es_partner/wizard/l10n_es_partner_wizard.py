# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
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
from openerp import tools
import os


class L10nEsPartnerImportWizard(orm.TransientModel):
    _name = 'l10n.es.partner.import.wizard'
    _inherit = 'res.config.installer'

    def execute(self, cr, uid, ids, context=None):
        super(L10nEsPartnerImportWizard, self).execute(cr, uid, ids,
                                                       context=context)
        try:
            path = os.path.join('l10n_es_partner', 'wizard', 'data_banks.xml')
            fp = tools.file_open(path)
            idref = {}
            tools.convert_xml_import(cr, 'l10n_es_partner', fp,  idref, 'init',
                                     noupdate=True)
        except IOError:
            pass
        finally:
            fp.close()

        return {}
