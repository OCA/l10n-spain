# -*- coding: utf-8 -*-
##############################################################################
#
#    Tecon Soluciones Informáticas, S.L.
#    http://www.tecon.es
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the Affero GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the Affero GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from openerp import models, fields


class ResCompany(models.Model):

    _inherit = 'res.company'

    facturae_cert = fields.Binary('Certificado firma electrónica',
                                  filters='*.pfx')
    facturae_cert_password = fields.Char('Contraseña certificado')
