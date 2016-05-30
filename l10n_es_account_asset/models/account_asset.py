# -*- coding: utf-8 -*-
# © 2012-2015 Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import calendar
from openerp import api, fields, models
from openerp.tools import float_is_zero
from dateutil.relativedelta import relativedelta


class AccountAssetCategory(models.Model):
    _inherit = 'account.asset.category'

    method_time = fields.Selection(
        selection_add=[('percentage', 'Fixed percentage')])
    method_percentage = fields.Float(
        string='Depreciation percentage', digits=(3, 2), default=100.0)

    _sql_constraints = [
        ('method_percentage',
         ' CHECK (method_percentage > 0 and method_percentage <= 100)',
         'Wrong percentage!'),
    ]


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    @api.multi
    def _get_last_depreciation_date(self):
        """Manipulate the date for getting the correct one when we define
        a start depreciation date.
        """
        last_depreciation_date = super(
            AccountAssetAsset, self)._get_last_depreciation_date()
        for asset in self:
            date = asset.start_depreciation_date
            if (date and (date > last_depreciation_date[asset.id] or
                          not asset.depreciation_line_ids)):
                last_depreciation_date[asset.id] = date
        return last_depreciation_date

    move_end_period = fields.Boolean(
        string="At the end of the period", default=True,
        help='Move the depreciation entry at the end of the period. If the '
             'period are 12 months, it is put on 31st of December, and in the '
             'end of the month in other case.')
    # Hay que definir un nuevo campo y jugar con los valores del antiguo
    # (method_time) para pasar el constraint _check_prorata y no tener que
    # modificar mucho código base
    method_time = fields.Selection(
        selection_add=[('percentage', 'Fixed percentage')])
    method_percentage = fields.Float(
        string='Depreciation percentage', digits=(3, 2), default=100.0)
    annual_percentage = fields.Float(
        string='Annual depreciation percentage', digits=(3, 2), default=100.0)
    start_depreciation_date = fields.Date(
        string='Start Depreciation Date', readonly=True,
        states={'draft': [('readonly', False)]},
        help="Only needed if not the same than purchase date")

    def _check_prorata(self, cr, uid, ids, context=None):
        for asset in self.browse(cr, uid, ids, context=context):
            if asset.prorata and asset.method_time not in ('number',
                                                           'percentage'):
                return False
        return True

    _constraints = [
        (_check_prorata, 'Prorata temporis can be applied only for time method'
         ' "number of depreciations".', ['prorata']),
    ]

    _sql_constraints = [
        ('method_percentage',
         ' CHECK (method_percentage > 0 and method_percentage <= 100)',
         'Wrong percentage!'),
    ]

    @api.multi
    def onchange_category_id(self, category_id):
        res = super(AccountAssetAsset, self).onchange_category_id(category_id)
        if category_id:
            category_obj = self.env['account.asset.category']
            category = category_obj.browse(category_id)
            res['value']['method_percentage'] = category.method_percentage
        return res

    @api.multi
    @api.onchange('method_percentage')
    def onchange_method_percentage(self):
        for asset in self:
            asset.annual_percentage = (
                asset.method_percentage * 12 / asset.method_period)

    @api.multi
    @api.onchange('annual_percentage')
    def onchange_annual_percentage(self):
        for asset in self:
            asset.method_percentage = (
                asset.annual_percentage * asset.method_period / 12)

    @api.model
    def _compute_board_undone_dotation_nb(self, asset, depreciation_date,
                                          total_days):
        if asset.method_time == 'percentage':
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
            return super(AccountAssetAsset, self).\
                _compute_board_undone_dotation_nb(
                asset, depreciation_date, total_days)

    @api.model
    def _compute_board_amount(self, asset, i, residual_amount, amount_to_depr,
                              undone_dotation_number,
                              posted_depreciation_line_ids, total_days,
                              depreciation_date):
        if asset.method_time == 'percentage':
            # Nuevo tipo de cálculo
            if i == undone_dotation_number:
                return residual_amount
            else:
                if i == 1 and asset.prorata:
                    if asset.method_period == 1:
                        total_days = calendar.monthrange(
                            depreciation_date.year, depreciation_date.month)[1]
                        days = total_days - float(depreciation_date.day) + 1
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
            depr_lin_obj = self.env['account.asset.depreciation.line']
            for line in depr_lin_obj.browse(posted_depreciation_line_ids):
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
            return super(AccountAssetAsset, self)._compute_board_amount(
                asset, i, residual_amount, amount_to_depr,
                undone_dotation_number, posted_depreciation_line_ids,
                total_days, depreciation_date)

    @api.multi
    def compute_depreciation_board(self):
        super(AccountAssetAsset, self).compute_depreciation_board()
        precision = self.env['decimal.precision'].precision_get('Account')
        for asset in self:
            if asset.depreciation_line_ids:
                last_depr = asset.depreciation_line_ids[-1]
                if not last_depr.move_id and float_is_zero(
                        last_depr.amount, precision):
                    last_depr.unlink()
            if asset.move_end_period:
                # Reescribir la fecha de la depreciación
                depr_lin_obj = self.env['account.asset.depreciation.line']
                new_depr_lines = depr_lin_obj.search(
                    [('asset_id', '=', asset.id), ('move_id', '=', False)])
                # En el caso de que la fecha de última amortización no sea
                # la de compra se debe generar el cuadro al período siguiente
                depreciation_date = fields.Date.from_string(
                    asset._get_last_depreciation_date()[asset.id])
                nb = 0
                for depr_line in new_depr_lines:
                    depr_date = fields.Date.from_string(
                        depr_line.depreciation_date)
                    if asset.method_period == 12:
                        depr_date = depr_date.replace(depr_date.year, 12, 31)
                    else:
                        if not asset.prorata:
                            if depr_date.day != 1:
                                depr_date = depreciation_date + relativedelta(
                                    months=+ (asset.method_period * (nb + 1)))
                            else:
                                depr_date = depreciation_date + relativedelta(
                                    months=+ (asset.method_period * nb))
                            nb += 1
                        last_month_day = calendar.monthrange(
                            depr_date.year, depr_date.month)[1]
                        depr_date = depr_date.replace(
                            depr_date.year, depr_date.month, last_month_day)
                    depr_line.depreciation_date = fields.Date.to_string(
                        depr_date)
        return True
