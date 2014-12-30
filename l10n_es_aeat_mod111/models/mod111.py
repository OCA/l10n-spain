# -*- encoding: utf-8 -*-
##############################################################################
#                                                                            #
#  OpenERP, Open Source Management Solution.                                 #
#                                                                            #
#  @author Carlos Sánchez Cifuentes <csanchez@grupovermon.com>               #
#                                                                            #
#  This program is free software: you can redistribute it and/or modify      #
#  it under the terms of the GNU Affero General Public License as            #
#  published by the Free Software Foundation, either version 3 of the        #
#  License, or (at your option) any later version.                           #
#                                                                            #
#  This program is distributed in the hope that it will be useful,           #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the              #
#  GNU Affero General Public License for more details.                       #
#                                                                            #
#  You should have received a copy of the GNU Affero General Public License  #
#  along with this program. If not, see <http://www.gnu.org/licenses/>.      #
#                                                                            #
##############################################################################

from openerp.osv import fields, orm


class L10nEsAeatMod111Report(orm.Model):

    _description = 'AEAT 111 report'

    _inherit = 'l10n.es.aeat.report'

    _name = 'l10n.es.aeat.mod111.report'

    _columns = {
        'apellidos_razon_social': fields.char(
            'Apellidos o razón social', size=30, readonly=True,
            states={'draft': [('readonly', False)]}, required=True),
        'calculation_date': fields.datetime('Fecha de cálculo'),
        'casilla_01': fields.integer('Casilla [01]', readonly=True),
        'casilla_02': fields.float('Casilla [02]', readonly=True),
        'casilla_03': fields.float('Casilla [03]', readonly=True),
        'casilla_04': fields.integer('Casilla [04]', readonly=True),
        'casilla_05': fields.float('Casilla [05]', readonly=True),
        'casilla_06': fields.float('Casilla [06]', readonly=True),
        'casilla_07': fields.integer('Casilla [07]', readonly=True),
        'casilla_08': fields.float('Casilla [08]', readonly=True),
        'casilla_09': fields.float('Casilla [09]', readonly=True),
        'casilla_10': fields.integer('Casilla [10]', readonly=True),
        'casilla_11': fields.float('Casilla [11]', readonly=True),
        'casilla_12': fields.float('Casilla [12]', readonly=True),
        'casilla_13': fields.integer('Casilla [13]', readonly=True),
        'casilla_14': fields.float('Casilla [14]', readonly=True),
        'casilla_15': fields.float('Casilla [15]', readonly=True),
        'casilla_16': fields.integer('Casilla [16]', readonly=True),
        'casilla_17': fields.float('Casilla [17]', readonly=True),
        'casilla_18': fields.float('Casilla [18]', readonly=True),
        'casilla_19': fields.integer('Casilla [19]', readonly=True),
        'casilla_20': fields.float('Casilla [20]', readonly=True),
        'casilla_21': fields.float('Casilla [21]', readonly=True),
        'casilla_22': fields.integer('Casilla [22]', readonly=True),
        'casilla_23': fields.float('Casilla [23]', readonly=True),
        'casilla_24': fields.float('Casilla [24]', readonly=True),
        'casilla_25': fields.integer('Casilla [25]', readonly=True),
        'casilla_26': fields.float('Casilla [26]', readonly=True),
        'casilla_27': fields.float('Casilla [27]', readonly=True),
        'casilla_28': fields.float('Casilla [28]', readonly=True),
        'casilla_29': fields.float('Casilla [29]', readonly=True),
        'casilla_30': fields.float('Casilla [30]', readonly=True),
        'codigo_electronico_anterior': fields.char(
            'Código electrónico', size=16, readonly=True,
            states={'draft': [('readonly', False)]},
            help='Código electrónico de la declaración anterior'
            ' (si se presentó telemáticamente).'
            ' A cumplimentar sólo en el caso de declaración complementaria.'),
        'company_id': fields.many2one(
            'res.company', 'Compañía', readonly=True,
            states={'draft': [('readonly', False)]}, required=True),
        'company_vat': fields.char(
            'NIF', size=9, readonly=True,
            states={'draft': [('readonly', False)]}, required=True),
        'complementaria': fields.boolean(
            'Declaración complementaria', readonly=True,
            states={'draft': [('readonly', False)]},
            help='Si esta predeclaración es complementaria de otra'
            ' autoliquidación anterior correspondiente al mismo concepto'
            ', ejercicio y período, indíquelo marcando esta casilla'),
        'currency_id': fields.related(
            'company_id', 'currency_id', type='many2one',
            relation='res.currency', string='Moneda', store=True),
        'fiscalyear_id': fields.many2one(
            'account.fiscalyear', 'Año fiscal', readonly=True,
            states={'draft': [('readonly', False)]}, required=True),
        'nombre': fields.char(
            'Nombre', size=15, readonly=True,
            states={'draft': [('readonly', False)]}, required=True),
        'numero_justificante_anterior': fields.char(
            'Número de justificante', size=13, readonly=True,
            states={'draft': [('readonly', False)]},
            help='Número de justificante de la declaración anterior'
            ' (si se presentó en papel).'
            ' A cumplimentar sólo en el caso de declaración complementaria.'),
        'periodo': fields.selection(
            [('1T', 'Primer trimestre'), ('2T', 'Segundo trimestre'),
                ('3T', 'Tercer trimestre'), ('4T', 'Cuarto trimestre'),
                ('01', 'Enero'), ('02', 'Febrero'), ('03', 'Marzo'),
                ('04', 'Abril'), ('05', 'Mayo'), ('06', 'Junio'),
                ('07', 'Julio'), ('08', 'Agosto'), ('09', 'Septiembre'),
                ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre')],
            'Período', readonly=True,
            states={'draft': [('readonly', False)]}, required=True),
        'state': fields.selection(
            [('draft', 'Borrador'), ('calculated', 'Procesada'),
                ('done', 'Realizada'), ('cancelled', 'Cancelada')],
            'Estado', readonly=True),
        'tipo_declaracion': fields.selection(
            [('I', 'Ingreso'), ('U', 'Domiciliación'),
                ('G', 'Ingreso a anotar en CCT'), ('N', 'Negativa')],
            'Tipo de declaración', readonly=True,
            states={'draft': [('readonly', False)]}, required=True),
    }

    def _check_complementary(self, cr, uid, ids, context=None):
        for report in self.read(cr, uid, ids, [
            'complementaria', 'codigo_electronico_anterior',
                'numero_justificante_anterior'], context=context):
            if (report['complementaria']
                and not report['codigo_electronico_anterior']
                    and not report['numero_justificante_anterior']):
                return False
        return True

    _constraints = [
        (_check_complementary,
            'Si se marca la casilla de liquidación complementaria,'
            ' debe rellenar el código electrónico o'
            ' el número de justificante de la declaración anterior.',
            ['codigo_electronico_anterior', 'numero_justificante_anterior']),
    ]

    _defaults = {
        'company_id': lambda self, cr, uid, context=None:
            (self.pool['res.company']._company_default_get(
                cr, uid, 'l10n.es.aeat.mod111.report', context=context)),
        'complementaria': False,
        'number': '111',
        'state': 'draft',
    }
