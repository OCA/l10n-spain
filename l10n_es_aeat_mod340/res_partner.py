# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2011 Acysos S.L. (http://acysos.com)
#                       Ignacio Ibeas <ignacio@acysos.com>
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
from openerp.osv import orm, fields


class ResPartner(orm.Model):
    """Extends partner to add fields used by the 340 report."""
    _inherit = "res.partner"

    _columns = {
        'vat_type': fields.selection(
            [('1', '1 - Corresponde a un NIF'),
             ('2', '2 - Se consigna el NIF/IVA (NIF OPERADOR '
              'INTRACOMUNITARIO)'),
             ('3', '3 - Pasaporte'),
             ('4', '4 - Documento oficial de identificación expedido por el '
              'país'),
             ('5', '5 - Certificado de residencia fiscal'),
             ('6', '6 - Otro documento probatorio')],
            'Clave tipo de NIF', help="Clave número de identificación en el "
            "país de residencia. Modelo 340."),
    }

    _defaults = {
        'vat_type': '1',
    }
