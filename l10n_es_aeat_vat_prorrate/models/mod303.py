# -*- coding: utf-8 -*-
# Copyright 2015 AvanzOSC - Ainara Galdona
# Copyright 2015-2017 Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import _, api, fields, exceptions, models

PRORRATE_TAX_LINE_MAPPING = {
    29: 28,
    33: 32,
    35: 34,
    37: 36,
    39: 38,
    41: 40,
}

PRORRATE_TAX_CODES = {
    # Casillas 28/29
    'SOICC': 'OICBI',
    'SOICC4': 'OICBI4',
    'SOICC10': 'OICBI10',
    'SOICC21': 'OICBI21',
    'REDC': 'REDBI',
    'REDC014': 'REDBI014',
    'REDC05': 'REDBI05',
    'REDC52': 'REDBI52',
    # Casillas 32/33
    'DIBYSCC': 'IBYSCBI',
    'DIBYSCC4': 'IBYSCBI4',
    'DIBYSCC10': 'IBYSCBI10',
    'DIBYSCC21': 'IBYSCBI21',
    # Casillas 34/35
    'DIBIC': 'IBIBI',
    'DIBIC4': 'IBIBI4',
    'DIBIC10': 'IBIBI10',
    'DIBIC21': 'IBIBI21',
    # Casillas 36/37
    'AIBYSCC': 'AIBYSCBI',
    'AIBYSCC4': 'AIBYSCBI4',
    'AIBCC4': 'AIBCBI4',
    'AISCC4': 'AISCBI4',
    'AIBYSCC10': 'AIBYSCBI10',
    'AIBCC10': 'AIBCBI10',
    'AISCC10': 'AISCBI10',
    'AIBYSCC21': 'AIBYSCBI21',
    'AIBCC21': 'AIBCBI21',
    'AISCC21': 'AISCBI21',
    # Casillas 38/39
    'AIBIC': 'AIBIBI',
    'AIBIC4': 'AIBIBI4',
    'AIBIC10': 'AIBIBI10',
    'AIBIC21': 'AIBIBI21',
    # Casillas 40/41
    # TODO: Puesto que todos comparten la base, esto no es exacto del todo
    'RDDSC': 'RDDSBI',
    'RDDSC4B': 'RDDSBI',
    'RDDSC4BI': 'RDDSBI',
    'RDDSC4EB': 'RDDSBI',
    'RDDSC4EBI': 'RDDSBI',
    'RDDSC4ES': 'RDDSBI',
    'RDDSC4IB': 'RDDSBI',
    'RDDSC4IBI': 'RDDSBI',
    'RDDSC4IS': 'RDDSBI',
    'RDDSC4ISP': 'RDDSBI',
    'RDDSC4S': 'RDDSBI',
    'RDDSC10B': 'RDDSBI',
    'RDDSC10BI': 'RDDSBI',
    'RDDSC10EB': 'RDDSBI',
    'RDDSC10EBI': 'RDDSBI',
    'RDDSC10ES': 'RDDSBI',
    'RDDSC10IB': 'RDDSBI',
    'RDDSC10IBI': 'RDDSBI',
    'RDDSC10IS': 'RDDSBI',
    'RDDSC10ISP': 'RDDSBI',
    'RDDSC10S': 'RDDSBI',
    'RDDSC21B': 'RDDSBI',
    'RDDSC21BI': 'RDDSBI',
    'RDDSC21EB': 'RDDSBI',
    'RDDSC21EBI': 'RDDSBI',
    'RDDSC21ES': 'RDDSBI',
    'RDDSC21IB': 'RDDSBI',
    'RDDSC21IBI': 'RDDSBI',
    'RDDSC21IS': 'RDDSBI',
    'RDDSC21ISP': 'RDDSBI',
    'RDDSC21S': 'RDDSBI',
    'RDDSCRE014': 'RDDSBI',
    'RDDSCRE05': 'RDDSBI',
    'RDDSCRE52': 'RDDSBI',
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
        string=u"[44] Regularización de la prorrata", default=0,
        states={'done': [('readonly', True)]},
        help=u"Regularización por aplicación del porcentaje definitivo de "
             u"prorrata.")
    vat_prorrate_type = fields.Selection(
        [('none', 'None'),
         ('general', 'General prorrate'), ],
        # ('special', 'Special prorrate')],
        readonly=True, states={'draft': [('readonly', False)]},
        string="VAT prorrate type", default='none', required=True)
    vat_prorrate_percent = fields.Float(
        string="VAT prorrate percentage", default=100,
        readonly=True, states={'draft': [('readonly', False)]})
    prorrate_regularization_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Prorrate regularization account",
        help="This account will be the one where charging the "
             "regularization of VAT prorrate.",
    )
    prorrate_regularization_analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Prorrate regularization analytic account",
        help="This analytic account will be the one where charging the "
             "regularization of the VAT prorrate.",
    )

    @api.constrains('vat_prorrate_percent')
    def check_vat_prorrate_percent(self):
        if not (0 < self.vat_prorrate_percent <= 100):
            raise exceptions.Warning(
                _('VAT prorrate percent must be between 0.01 and 100'))

    @api.multi
    def _calculate_casilla_44(self):
        self.ensure_one()
        self.casilla_44 = 0
        if (self.vat_prorrate_type != 'general' or
                self.period_type not in ('4T', '12')):
            return
        # Get prorrate from previous declarations
        min_date = min(self.periods.mapped('date_start'))
        prev_reports = self._get_previous_fiscalyear_reports(min_date)
        if any(x.state == 'draft' for x in prev_reports):
            raise exceptions.Warning(
                _("There's at least one previous report in draft state. "
                  "Please confirm it before making this one.")
            )
        for prev_report in prev_reports:
            diff_perc = (self.vat_prorrate_percent -
                         prev_report.vat_prorrate_percent)
            if diff_perc:
                self.casilla_44 += (
                    diff_perc * prev_report.total_deducir /
                    prev_report.vat_prorrate_percent)

    @api.multi
    def calculate(self):
        res = super(L10nEsAeatMod303Report, self).calculate()
        for report in self:
            report._calculate_casilla_44()
            account_number = '6391%' if report.casilla_44 > 0 else '6341%'
            # Choose default account according result
            report.prorrate_regularization_account_id = (
                self.env['account.account'].search([
                    ('code', 'like', account_number),
                    ('company_id', '=', report.company_id.id),
                    ('type', '!=', 'view'),
                ], limit=1)
            )
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
        move_line_obj = self.env['account.move.line']
        tax_code_obj = self.env['account.tax.code']
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
            tax_account_groups = move_line_obj.read_group(
                [('id', 'in', tax_line.move_lines.ids)],
                ['debit', 'credit', 'tax_code_id'],
                ['tax_code_id'],
            )
            total_prorrate = 0
            extra_lines = []
            # Split by tax code for having the proportional part
            for tax_account_group in tax_account_groups:
                tax_code = tax_code_obj.browse(
                    tax_account_group['tax_code_id'][0]
                )
                base_tax_code_code = PRORRATE_TAX_CODES[tax_code.code]
                base_tax_code = tax_code_obj.search(
                    [('code', '=', base_tax_code_code)], limit=1,
                )
                prorrate_debit = tax_account_group['debit']
                prorrate_credit = tax_account_group['credit']
                prec = self.env['decimal.precision'].precision_get('Account')
                subtotal_prorrate = round(
                    (prorrate_debit - prorrate_credit) * factor, prec,
                )
                total_prorrate += subtotal_prorrate
                account_groups = move_line_obj.read_group(
                    [
                        ('id', 'in', base_tax_line.move_lines.ids),
                        ('tax_code_id', '=', base_tax_code.id)
                    ],
                    ['tax_amount', 'account_id', 'analytic_account_id'],
                    ['account_id', 'analytic_account_id'],
                )
                total_balance = sum(x['tax_amount'] for x in account_groups)
                amount_factor = abs(subtotal_prorrate) / abs(total_balance)
                for account_group in account_groups:
                    analytic_groups = move_line_obj.read_group(
                        account_group['__domain'],
                        ['tax_amount', 'analytic_account_id'],
                        ['analytic_account_id'],
                    )
                    for analytic_group in analytic_groups:
                        balance = analytic_group['tax_amount'] * amount_factor
                        move_line_vals = {
                            'name': account_group['account_id'][1],
                            'account_id': account_group['account_id'][0],
                            'debit': (
                                round(balance, prec) if balance > 0 else 0
                            ),
                            'credit': (
                                round(-balance, prec) if balance < 0 else 0
                            ),
                        }
                        if analytic_group['analytic_account_id']:
                            move_line_vals['analytic_account_id'] = (
                                analytic_group['analytic_account_id'])[0]
                        extra_lines.append(move_line_vals)
            # Add/substract possible rounding inaccuracy to the first line
            extra_lines = self._prorrate_diff_distribution(
                total_prorrate, extra_lines,
            )
            all_lines += extra_lines
        return all_lines

    def _prorrate_diff_distribution(self, prorrate, extra_lines):
        if not extra_lines:
            # If no lines, then we can not distribute nothing
            return extra_lines
        prec = self.env['decimal.precision'].precision_get('Account')
        extra_debit = sum(x['debit'] for x in extra_lines)
        extra_credit = sum(x['credit'] for x in extra_lines)
        extra_balance = extra_debit - extra_credit
        diff = round(prorrate - extra_balance, prec)
        if prorrate < 0:
            column = 'credit'
        else:
            column = 'debit'
        n = 0
        count = len(extra_lines)
        step = 1. / (10 ** prec)
        if diff < 0:
            step = -step
        while abs(diff) > 0:
            # We need to add some in order to get prorrate
            line = extra_lines[n]
            next_value = round(line[column] + step, prec)
            if line[column] and next_value:
                line[column] = next_value
                diff = round(diff - step, prec)
            n = (n + 1) % count
        return extra_lines

    @api.multi
    def _prepare_regularization_extra_move_lines(self):
        lines = super(L10nEsAeatMod303Report,
                      self)._prepare_regularization_extra_move_lines()
        if self.casilla_44:
            lines.append({
                'name': _('Regularización prorrata IVA'),
                'account_id': self.prorrate_regularization_account_id.id,
                'analytic_account_id': (
                    self.prorrate_regularization_analytic_account_id.id
                ),
                'debit': -self.casilla_44 if self.casilla_44 < 0 else 0.0,
                'credit': self.casilla_44 if self.casilla_44 > 0 else 0.0,
            })
        return lines
