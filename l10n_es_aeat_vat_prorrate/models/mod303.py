# -*- coding: utf-8 -*-
# © 2015-2016 Antiun Ingeniería S.L. - Pedro M. Baeza
# © 2015 AvanzOSC - Ainara Galdona
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api, exceptions, _

PRORRATE_TAX_LINE_MAPPING = {
    29: 28,
    33: 32,
    35: 34,
    37: 36,
    39: 38,
    41: 40,
}


class L10nEsAeatMod303Report(models.Model):
    _inherit = 'l10n.es.aeat.mod303.report'

    @api.multi
    @api.depends('tax_lines', 'tax_lines.amount', 'casilla_44')
    def _compute_total_deducir(self):
        super(L10nEsAeatMod303Report, self)._compute_total_deducir()
        for report in self:
            report.total_deducir += report.casilla_44

    casilla_44 = fields.Float(
        string="[44] Regularización de la prorrata", default=0,
        states={'done': [('readonly', True)]},
        help="Regularizacion por aplicación del porcentaje definitivo de "
             "prorrata.")
    vat_prorrate_type = fields.Selection(
        [('none', 'None'),
         ('general', 'General prorrate'), ],
        # ('special', 'Special prorrate')],
        readonly=True, states={'draft': [('readonly', False)]},
        string="VAT prorrate type", default='none', required=True)
    vat_prorrate_percent = fields.Float(
        string="VAT prorrate percentage", default=100,
        readonly=True, states={'draft': [('readonly', False)]})

    @api.constrains('vat_prorrate_percent')
    def check_vat_prorrate_percent(self):
        if self.vat_prorrate_percent < 0 or self.vat_prorrate_percent > 100:
            raise exceptions.Warning(
                _('VAT prorrate percent must be between 0 and 100'))

    @api.multi
    def calculate(self):
        res = super(L10nEsAeatMod303Report, self).calculate()
        for report in self:
            report.casilla_44 = 0
            if (report.vat_prorrate_type != 'general' or
                    report.period_type not in ('4T', '12')):
                continue
            # Get prorrate from previous declarations
            min_date = min(report.periods.mapped('date_start'))
            prev_reports = report._get_previous_fiscalyear_reports(min_date)
            if any(x.state == 'draft' for x in prev_reports):
                raise exceptions.Warning(
                    _("There's at least one previous report in draft state. "
                      "Please confirm it before making this one."))
            for prev_report in prev_reports:
                diff_perc = (report.vat_prorrate_percent -
                             prev_report.vat_prorrate_percent)
                if diff_perc:
                    report.casilla_44 += (
                        diff_perc * prev_report.total_deducir /
                        prev_report.vat_prorrate_percent)
        return res

    @api.multi
    def _prepare_tax_line_vals(self, map_line):
        res = super(L10nEsAeatMod303Report, self)._prepare_tax_line_vals(
            map_line)
        if (self.vat_prorrate_type == 'general' and
                map_line.field_number in PRORRATE_TAX_LINE_MAPPING.keys()):
            res['amount'] *= self.vat_prorrate_percent / 100
        return res

    @api.multi
    def _process_tax_line_regularization(self, tax_lines):
        """Añadir la parte no deducida de la base como gasto repartido
        proporcionalmente entre las cuentas de las líneas de gasto existentes.
        """
        all_lines = []
        for tax_line in tax_lines:
            # We need to treat each tax_line independently
            lines = super(L10nEsAeatMod303Report,
                          self)._process_tax_line_regularization(tax_line)
            all_lines += lines
            if (self.vat_prorrate_type != 'general' or
                    tax_line.field_number not in
                    PRORRATE_TAX_LINE_MAPPING.keys()):
                continue
            factor = (100 - self.vat_prorrate_percent) / 100
            base_tax_line = self.tax_lines.filtered(
                lambda x: x.field_number == PRORRATE_TAX_LINE_MAPPING[
                    tax_line.field_number])
            if not base_tax_line.move_lines:
                continue
            prorrate_debit = sum(x['debit'] for x in lines)
            prorrate_credit = sum(x['credit'] for x in lines)
            prec = self.env['decimal.precision'].precision_get('Account')
            total_prorrate = round(
                (prorrate_debit - prorrate_credit) * factor, prec)
            account_groups = self.env['account.move.line'].read_group(
                [('id', 'in', base_tax_line.move_lines.ids)],
                ['tax_amount', 'account_id', 'account_analytic_id'],
                ['account_id', 'account_analytic_id'])
            total_balance = sum(x['tax_amount'] for x in account_groups)
            extra_lines = []
            amount_factor = abs(total_prorrate) / abs(total_balance)
            for account_group in account_groups:
                analytic_groups = self.env['account.move.line'].read_group(
                    account_group['__domain'],
                    ['tax_amount', 'analytic_account_id'],
                    ['analytic_account_id'])
                for analytic_group in analytic_groups:
                    balance = analytic_group['tax_amount'] * amount_factor
                    move_line_vals = {
                        'name': account_group['account_id'][1],
                        'account_id': account_group['account_id'][0],
                        'debit': round(balance, prec) if balance > 0 else 0,
                        'credit': round(-balance, prec) if balance < 0 else 0,
                    }
                    if analytic_group['analytic_account_id']:
                        move_line_vals['analytic_account_id'] = (
                            analytic_group['analytic_account_id'])[0]
                    extra_lines.append(move_line_vals)
            # Add/substract possible rounding inaccuracy to the first line
            extra_lines = self._prorrate_diff_distribution(
                total_prorrate, extra_lines)
            all_lines += extra_lines
        return all_lines

    def _prorrate_diff_distribution(self, prorrate, extra_lines):
        count = len(extra_lines)
        if not count:
            # If no lines, then we can not distribute nothing
            return extra_lines
        prec = self.env['decimal.precision'].precision_get('Account')
        extra_debit = sum(x['debit'] for x in extra_lines)
        extra_credit = sum(x['credit'] for x in extra_lines)
        extra = extra_debit - extra_credit
        diff = round(((-1) * prorrate) - extra, prec)
        if prorrate > 0:
            column = 'credit'
            diff = (-1) * diff
        else:
            column = 'debit'
        n = 0
        step = 1. / (10 ** prec)
        if diff < 0:
            step = (-1) * step
        while abs(diff) > 0:
            # We need to add some in order to get prorrate
            line = extra_lines[n]
            next_value = round(line[column] + step, prec)
            if line[column] and next_value:
                line[column] = next_value
                diff = round(diff - step, prec)
            n += 1
            if n >= count:
                # Wrap to first line when last line reached
                n = 0
        return extra_lines

    @api.multi
    def _prepare_regularization_extra_move_lines(self):
        lines = super(L10nEsAeatMod303Report,
                      self)._prepare_regularization_extra_move_lines()
        if self.casilla_44:
            account_number = '6391%' if self.casilla_44 > 0 else '6341%'
            lines.append({
                'name': _('Regularización prorrata IVA'),
                'account_id': self.env['account.account'].search(
                    [('code', 'like', account_number),
                     ('company_id', '=', self.company_id.id),
                     ('type', '!=', 'view')], limit=1).id,
                'debit': -self.casilla_44 if self.casilla_44 < 0 else 0.0,
                'credit': self.casilla_44 if self.casilla_44 > 0 else 0.0,
            })
        return lines
