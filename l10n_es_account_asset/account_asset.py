# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2012 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
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
import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DSDF


class account_asset_category(orm.Model):
    _inherit = 'account.asset.category'

    _columns = {
        'ext_method_time': fields.selection(
            [('number', 'Number of Depreciations'),
             ('end', 'Ending Date'),
             ('percentage', 'Fixed percentage')], 'Time Method', required=True,
            help="Choose the method to use to compute the dates and number of "
                 "depreciation lines.\n"
                 "  * Number of Depreciations: Fix the number of depreciation "
                 "lines and the time between 2 depreciations.\n"
                 "  * Ending Date: Choose the time between 2 depreciations "
                 "and the date the depreciations won't go beyond.\n"
                 "  * Fixed percentage: Choose the time between 2 "
                 "depreciations and the percentage to depreciate."),
        'method_percentage': fields.float('Depreciation percentage',
                                          digits=(3, 2)),
    }

    _defaults = {
        'method_percentage': 100.0,
        'ext_method_time': 'percentage',
    }

    _sql_constraints = [
        ('method_percentage',
         ' CHECK (method_percentage > 0 and method_percentage <= 100)',
         'Wrong percentage!'),
    ]

    def onchange_ext_method_time(self, cr, uid, ids, ext_method_time,
                                 context=None):
        res = {'value': {}}
        res['value']['method_time'] = ('end' if ext_method_time == 'end' else
                                       'number')
        return res


class account_asset_asset(orm.Model):
    _inherit = 'account.asset.asset'

    def _get_last_depreciation_date(self, cr, uid, ids, context=None):
        """
        @param id: ids of a account.asset.asset objects
        @return: Returns a dictionary of the effective dates of the last
        depreciation entry made for given asset ids. If there isn't any,
        return the purchase date of this asset
        """

        last_depreciation_date = super(
            account_asset_asset, self)._get_last_depreciation_date(
                cr, uid, ids, context=context)
        for asset in self.browse(cr, uid, ids, context=context):
            if asset.start_depreciation_date and (
                asset.start_depreciation_date >
                    last_depreciation_date[asset.id]):
                last_depreciation_date[asset.id] = \
                    asset.start_depreciation_date
        return last_depreciation_date

    _columns = {
        'move_end_period': fields.boolean(
            "At the end of the period",
            help='Move the depreciation entry at the end of the period. If '
                 'the period are 12 months, it is put on 31st of December, '
                 'and in the end of the month in other case.'),
        # Hay que definir un nuevo campo y jugar con los valores del antiguo
        # (method_time) para pasar el constraint _check_prorata y no tener que
        # modificar mucho código base
        'ext_method_time': fields.selection(
            [('number', 'Number of Depreciations'),
             ('end', 'Ending Date'),
             ('percentage', 'Fixed percentage')], 'Time Method', required=True,
            help="Choose the method to use to compute the dates and number of "
                 "depreciation lines.\n"
                 "  * Number of Depreciations: Fix the number of depreciation "
                 "lines and the time between 2 depreciations.\n"
                 "  * Ending Date: Choose the time between 2 depreciations "
                 "and the date the depreciations won't go beyond.\n"
                 "  * Fixed percentage: Choose the time between 2 "
                 "depreciations and the percentage to depreciate."),
        'method_percentage': fields.float('Depreciation percentage',
                                          digits=(3, 2)),
        'start_depreciation_date': fields.date(
            'Start Depreciation Date',
            readonly=True,
            states={'draft': [('readonly', False)]},
            help="Only needed if not the same than purchase date"),

    }

    _defaults = {
        'method_percentage': 100.0,
        'move_end_period': True,
    }

    _sql_constraints = [
        ('method_percentage',
         ' CHECK (method_percentage > 0 and method_percentage <= 100)',
         'Wrong percentage!'),
    ]

    def onchange_ext_method_time(self, cr, uid, ids, ext_method_time,
                                 context=None):
        res = {'value': {}}
        res['value']['method_time'] = ('end' if ext_method_time == 'end'
                                       else 'number')
        return res

    def onchange_category_id(self, cr, uid, ids, category_id, context=None):
        res = super(account_asset_asset, self).onchange_category_id(
            cr, uid, ids, category_id, context=context)
        if category_id:
            category_obj = self.pool.get('account.asset.category')
            category = category_obj.browse(cr, uid, category_id,
                                           context=context)
            res['value']['ext_method_time'] = category.ext_method_time
            res['value']['method_percentage'] = category.method_percentage
        return res

    def _compute_board_undone_dotation_nb(self, cr, uid, asset,
                                          depreciation_date, total_days,
                                          context=None):
        if asset.ext_method_time == 'percentage':
            number = 0
            percentage = 100.0
            while percentage > 0:
                if number == 0 and asset.prorata:
                    days = (total_days -
                            float(depreciation_date.strftime('%j'))) + 1
                    percentage -= asset.method_percentage * days / total_days
                else:
                    percentage -= asset.method_percentage
                number += 1
            return number
        else:
            val = super(account_asset_asset, self).\
                _compute_board_undone_dotation_nb(cr, uid, asset,
                                                  depreciation_date,
                                                  total_days, context=context)
            if depreciation_date.day == 1 and depreciation_date.month == 1 \
                    and asset.method_period == 12:
                # Quitar una depreciación del nº total si el activo se compró
                # el 1 de enero, ya que ese año sería completo
                val -= 1
            return val

    def _compute_board_amount(self, cr, uid, asset, i, residual_amount,
                              amount_to_depr, undone_dotation_number,
                              posted_depreciation_line_ids, total_days,
                              depreciation_date, context=None):
        if asset.ext_method_time == 'percentage':
            # Nuevo tipo de cálculo
            if i == undone_dotation_number:
                return residual_amount
            else:
                if i == 1 and asset.prorata:
                    if asset.method_period == 1:
                        total_days = calendar.monthrange(
                            depreciation_date.year, depreciation_date.month)[1]
                        days = total_days - float(depreciation_date.day)
                    else:
                        days = (total_days - float(
                            depreciation_date.strftime('%j'))) + 1
                    percentage = asset.method_percentage * days / total_days
                else:
                    percentage = asset.method_percentage
                return amount_to_depr * percentage / 100
        elif (asset.method == 'linear' and asset.prorata and
              i != undone_dotation_number):
            # Caso especial de cálculo que cambia
            # Debemos considerar también las cantidades ya depreciadas
            depreciated_amount = 0
            depr_lin_obj = self.pool['account.asset.depreciation.line']
            for line in depr_lin_obj.browse(cr, uid,
                                            posted_depreciation_line_ids):
                depreciated_amount += line.amount
            amount = (amount_to_depr + depreciated_amount) \
                / asset.method_number
            if i == 1:
                if asset.method_period == 1:
                        total_days = calendar.monthrange(
                            depreciation_date.year, depreciation_date.month)[1]
                        days = total_days - float(depreciation_date.day) + 1
                else:
                    days = (total_days -
                            float(depreciation_date.strftime('%j'))) + 1
                amount *= days / total_days
            return amount
        else:
            return super(account_asset_asset, self)._compute_board_amount(
                cr, uid, asset, i, residual_amount, amount_to_depr,
                undone_dotation_number, posted_depreciation_line_ids,
                total_days, depreciation_date, context=context)

    def compute_depreciation_board(self, cr, uid, ids, context=None):
        super(account_asset_asset, self).compute_depreciation_board(
            cr, uid, ids, context=context)
        for asset in self.browse(cr, uid, ids, context=context):
            if asset.move_end_period:
                # Reescribir la fecha de la depreciación
                depr_lin_obj = self.pool['account.asset.depreciation.line']
                new_depr_line_ids = depr_lin_obj.search(
                    cr, uid, [('asset_id', '=', asset.id),
                              ('move_id', '=', False)], context=context)

                # En el caso de que la fecha de última amortización no sea
                # la de compra se debe generar el cuadro
                # al período siguiente
                depreciation_date = datetime.strptime(
                    self._get_last_depreciation_date(cr, uid, [asset.id],
                                                     context)[asset.id],
                    '%Y-%m-%d')
                fix_depreciation = False

                initial_date = asset.start_depreciation_date or\
                    asset.purchase_date

                if (depreciation_date != datetime.strptime(
                        initial_date, '%Y-%m-%d')):
                    fix_depreciation = True
                nb = 0
                for depr_line in depr_lin_obj.browse(cr, uid,
                                                     new_depr_line_ids):
                    depr_date = datetime.strptime(
                        depr_line.depreciation_date, DSDF)
                    if fix_depreciation:
                        if depr_date.day != 1:
                            depr_date = depr_date + relativedelta(
                                months=+asset.method_period)
                    if asset.method_period == 12:
                        depr_date = depr_date.replace(depr_date.year, 12, 31)
                    else:
                        if not asset.prorata:
                            if depr_date.day != 1:
                                depr_date = depreciation_date + relativedelta(
                                    months=+ (asset.method_period * (nb+1)))
                            else:
                                depr_date = depreciation_date + relativedelta(
                                    months=+ (asset.method_period * nb))
                            nb += 1
                        last_month_day = calendar.monthrange(
                            depr_date.year, depr_date.month)[1]
                        depr_date = depr_date.replace(
                            depr_date.year, depr_date.month, last_month_day)
                    depr_lin_obj.write(
                        cr, uid, depr_line.id,
                        {'depreciation_date': depr_date.strftime(DSDF)})
        return True
