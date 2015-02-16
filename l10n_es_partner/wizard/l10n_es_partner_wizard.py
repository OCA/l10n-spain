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
from openerp import models, fields, api, _
from openerp import tools
from ..gen_src.gen_data_banks import gen_bank_data_xml
import tempfile
import os


class L10nEsPartnerImportWizard(models.TransientModel):
    _name = 'l10n.es.partner.import.wizard'
    _inherit = 'res.config.installer'

    import_fail = fields.Boolean(default=False)

    @api.multi
    def import_local(self):
        res = super(L10nEsPartnerImportWizard, self).execute()
        path = os.path.join('l10n_es_partner', 'wizard', 'data_banks.xml')
        with tools.file_open(path) as fp:
            tools.convert_xml_import(
                self._cr, 'l10n_es_partner', fp, {}, 'init', noupdate=False)
        return res

    @api.multi
    def execute(self):
        import urllib2
        try:
            xlsfile = urllib2.urlopen(
                'http://www.bde.es/f/webbde/IFI/servicio/regis/ficheros/es/'
                'REGBANESP_CONESTAB_A.XLS')
            # Read XLS
            src_file = tempfile.NamedTemporaryFile(delete=False)
            src_file.write(xlsfile.read())
            src_file.close()
            # Prepare XML dest file
            dest_file = tempfile.NamedTemporaryFile('w', delete=False)
            dest_file.close()
            # Generate XML and reopen it
            gen_bank_data_xml(src_file.name, dest_file.name)
            tools.convert_xml_import(
                self._cr, 'l10n_es_partner', dest_file.name, {}, 'init',
                noupdate=False)
        except:
            self.import_fail = True
            return {
                'name': _('Import spanish bank data'),
                'type': 'ir.actions.act_window',
                'res_model': 'l10n.es.partner.import.wizard',
                'view_id': self.env.ref("l10n_es_partner."
                                        "l10n_es_partner_import_wizard").id,
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
            }
        finally:
            dest_file.close()
            os.remove(src_file.name)
            os.remove(dest_file.name)
