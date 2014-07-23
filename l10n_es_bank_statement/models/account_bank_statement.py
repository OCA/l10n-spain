# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) All rights reserved:
#        2013-2014 Servicios Tecnológicos Avanzados (http://serviciosbaeza.com)
#                  Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
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


class AccountBankStatementLine(orm.Model):
    _inherit = "account.bank.statement.line"

    _columns = {
        'c43_concept': fields.selection(
            [('01', 'Reintegro/Talón'),
             ('02', 'Ingreso/Entrega/Abonaré'),
             ('03', 'Docimiliado/Recibo/Letra/Pago por su cta.'),
             ('04', 'Giro/Transferencia/Traspaso/Cheque'),
             ('05', 'Amortización préstamo'),
             ('06', 'Remesa efectos'),
             ('07', 'Subscripción/Div. pasivos/Canje'),
             ('08', 'Div. cupones/Prima junta/Amortización'),
             ('09', 'Compra/Venta valores'),
             ('10', 'Cheque gasolina'),
             ('11', 'Cajero automático'),
             ('12', 'Tarjeta crédito/débito'),
             ('13', 'Operaciones extranjero'),
             ('14', 'Devolución/Impagado'),
             ('15', 'Nómina/Seguro social'),
             ('16', 'Timbre/Corretaje/Póliza'),
             ('17', 'Intereses/Comisión/Custodia/Gastos/Impuestos'),
             ('98', 'Anulación/Corrección'),
             ('99', 'Varios')],
            'C43 concept', readonly=True),
    }

    _defaults = {
        'c43_concept': '99',
    }
