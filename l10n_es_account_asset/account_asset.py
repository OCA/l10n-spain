# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2012 Servicios Tecnológicos Avanzados (http://www.serviciosbaeza.com)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
import datetime
from osv import osv, fields

class account_asset_asset(osv.osv):
    _inherit = 'account.asset.asset'
    _name = 'account.asset.asset'
    _description = 'Asset'

    _columns = {
        'move_end_period': fields.boolean("At the end of the period", help='Move the depreciation entry at the end of the period. If the period are 12 months, it is put on 31st of December, and in the end of the month in other case.'),
    }
    
    _defaults = {
        'move_end_period': True,
    }

    def _compute_board_undone_dotation_nb(self, cr, uid, asset, depreciation_date, total_days, context=None):
        val = super(account_asset_asset, self)._compute_board_undone_dotation_nb(cr, uid, asset, depreciation_date, total_days, context=context)
        if depreciation_date.day == 1 and depreciation_date.month == 1:
            # Quitar una depreciación del nº total si el activo se compró el 1 de enero,
            # ya que ese año sería completo  
            val -= 1
        return val
    
    def _compute_board_amount(self, cr, uid, asset, i, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date, context=None):
        if asset.method == 'linear' and asset.prorata and i != undone_dotation_number:
            # Caso especial de cálculo que cambia
            amount = amount_to_depr / asset.method_number
            if i == 1:
                year = depreciation_date.year
                days = (total_days - float(depreciation_date.strftime('%j'))) + 1
                amount *= days / total_days
            return amount
        else:
            return super(account_asset_asset, self)._compute_board_amount(cr, uid, asset, i, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date, context=context)

    def compute_depreciation_board(self, cr, uid, ids, context=None):
        super(account_asset_asset, self).compute_depreciation_board(cr, uid, ids, context=context)
        for asset in self.browse(cr, uid, ids, context=context):
            if asset.move_end_period:
                # Reescribir la fecha de la depreciación
                depreciation_lin_obj = self.pool.get('account.asset.depreciation.line')
                new_depreciation_line_ids = depreciation_lin_obj.search(cr, uid, [('asset_id', '=', asset.id), ('move_id', '=', False)])
                for depreciation_line in depreciation_lin_obj.browse(cr, uid, new_depreciation_line_ids):
                    depreciation_date = datetime.datetime.strptime(depreciation_line.depreciation_date, '%Y-%m-%d') 
                    if asset.method_period == 12:
                        depreciation_date = depreciation_date.replace(depreciation_date.year, 12, 31)
                    else:
                        last_month_day = calendar.monthrange(depreciation_date.year, depreciation_date.month)[1]
                        depreciation_date = depreciation_date.replace(depreciation_date.year, depreciation_date.month, last_month_day)
                    depreciation_lin_obj.write(cr, uid, depreciation_line.id, {'depreciation_date': depreciation_date.strftime('%Y-%m-%d') })
        
        return True
        
account_asset_asset()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
