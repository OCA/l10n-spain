# -*- coding: utf-8 -*-
# © 2016 - Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, exceptions, fields, models, _
import openerp.addons.decimal_precision as dp


class L10nEsAeatReportTaxMapping(models.AbstractModel):
    _name = "l10n.es.aeat.report.tax.mapping"
    _inherit = "l10n.es.aeat.report"
    _description = ("Inheritable abstract model to add taxes by code mapping "
                    "in any AEAT report")

    tax_lines = fields.One2many(
        comodel_name='l10n.es.aeat.tax.line', inverse_name='res_id',
        domain=lambda self: [("model", "=", self._name)], auto_join=True,
        ondelete="cascade", readonly=True)

    @api.multi
    def calculate(self):
        res = super(L10nEsAeatReportTaxMapping, self).calculate()
        for report in self:
            report.tax_lines.unlink()
            # Buscar configuración de mapeo de impuestos
            tax_code_map_obj = self.env['aeat.mod.map.tax.code']
            date_start = min([fields.Date.from_string(x) for x in
                              self.periods.mapped('date_start')])
            date_stop = max([fields.Date.from_string(x) for x in
                             self.periods.mapped('date_stop')])
            tax_code_map = tax_code_map_obj.search(
                [('model', '=', report.number),
                 '|',
                 ('date_from', '<=', date_start),
                 ('date_from', '=', False),
                 '|',
                 ('date_to', '>=', date_stop),
                 ('date_to', '=', False)], limit=1)
            if tax_code_map:
                tax_lines = []
                for map_line in tax_code_map.map_lines:
                    tax_lines.append(report._prepare_tax_line_vals(map_line))
                report.tax_lines = [(0, 0, x) for x in tax_lines]
        return res

    @api.multi
    def _prepare_tax_line_vals(self, map_line):
        self.ensure_one()
        move_lines = self._get_tax_code_lines(
            map_line.mapped('tax_codes.code'), periods=self.periods)
        return {
            'model': self._name,
            'res_id': self.id,
            'map_line': map_line.id,
            'amount': sum(move_lines.mapped('tax_amount')),
            'move_lines': [(6, 0, move_lines.ids)],
        }

    @api.multi
    def _get_partner_domain(self):
        return []

    @api.multi
    def _get_move_line_domain(self, codes, periods=None,
                              include_children=True):
        self.ensure_one()
        tax_code_model = self.env['account.tax.code']
        tax_codes = tax_code_model.search(
            [('code', 'in', codes),
             ('company_id', 'child_of', self.company_id.id)])
        if include_children and tax_codes:
            tax_codes = tax_code_model.search(
                [('id', 'child_of', tax_codes.ids),
                 ('company_id', 'child_of', self.company_id.id)])
        if not periods:
            periods = self.env['account.period'].search(
                [('fiscalyear_id', '=', self.fiscalyear_id.id)])
        move_line_domain = [('company_id', 'child_of', self.company_id.id),
                            ('tax_code_id', 'child_of', tax_codes.ids),
                            ('period_id', 'in', periods.ids)]
        move_line_domain += self._get_partner_domain()
        return move_line_domain

    @api.model
    def _get_tax_code_lines(self, codes, periods=None, include_children=True):
        """
        Get the move lines for the codes and periods associated
        :param codes: List of strings for the tax codes
        :param periods: Periods to include
        :param include_children: True (default) if it also searches on
          children tax codes.
        :return: Move lines recordset that matches the criteria.
        """
        domain = self._get_move_line_domain(
            codes, periods=periods, include_children=include_children)
        return self.env['account.move.line'].search(domain)

    @api.model
    def _prepare_regularization_move_line(self, account_group):
        return {
            'name': account_group['account_id'][1],
            'account_id': account_group['account_id'][0],
            'debit': account_group['credit'],
            'credit': account_group['debit'],
        }

    @api.multi
    def _process_tax_line_regularization(self, tax_line):
        self.ensure_one()
        groups = self.env['account.move.line'].read_group(
            [('id', 'in', tax_line.move_lines.ids)],
            ['debit', 'credit', 'account_id'],
            ['account_id'])
        lines = []
        for group in groups:
            if group['debit'] > 0 and group['credit'] > 0:
                new_group = group.copy()
                group['debit'] = 0
                new_group['credit'] = 0
                lines.append(self._prepare_regularization_move_line(new_group))
            lines.append(self._prepare_regularization_move_line(group))
        return lines

    @api.model
    def _prepare_counterpart_move_line(self, account, debit, credit):
        vals = {
            'name': _('Regularization'),
            'account_id': account.id,
            'partner_id': self.env.ref('l10n_es_aeat.res_partner_aeat').id,
        }
        precision = self.env['decimal.precision'].precision_get('Account')
        balance = round(debit - credit, precision)
        vals['debit'] = 0.0 if debit > credit else -balance
        vals['credit'] = balance if debit > credit else 0.0
        return vals

    @api.multi
    def _prepare_regularization_extra_move_lines(self):
        return []

    @api.multi
    def _prepare_regularization_move_lines(self):
        """Prepare the list of dictionaries for the regularization move lines.
        """
        self.ensure_one()
        lines = []
        for tax_line in self.tax_lines.filtered('to_regularize'):
            result = self._process_tax_line_regularization(tax_line)
            # TODO: Ver si alguna vez se desglosa una cuenta en varias líneas
            # y agrupar en consecuencia
            lines += result
        lines += self._prepare_regularization_extra_move_lines()
        # Write counterpart with the remaining
        debit = sum(x['debit'] for x in lines)
        credit = sum(x['credit'] for x in lines)
        lines.append(self._prepare_counterpart_move_line(
            self.counterpart_account, debit, credit))
        return lines

    @api.one
    def create_regularization_move(self):
        if not self.counterpart_account or not self.journal_id:
            raise exceptions.Warning(
                _("You must fill both journal and counterpart account."))
        move_vals = self._prepare_move_vals()
        line_vals_list = self._prepare_regularization_move_lines()
        move_vals['line_id'] = [(0, 0, x) for x in line_vals_list]
        self.move_id = self.env['account.move'].create(move_vals)


class L10nEsAeatTaxLine(models.Model):
    _name = "l10n.es.aeat.tax.line"

    res_id = fields.Integer("Resource ID", index=True, required=True)
    field_number = fields.Integer(
        string="Field number", related="map_line.field_number",
        store=True)
    name = fields.Char(
        string="Name", related="map_line.name", store=True)
    amount = fields.Float(digits=dp.get_precision('Account'))
    map_line = fields.Many2one(
        comodel_name='aeat.mod.map.tax.code.line', required=True,
        ondelete="cascade")
    move_lines = fields.Many2many(
        comodel_name='account.move.line', string='Journal items')
    to_regularize = fields.Boolean(related='map_line.to_regularize')
    model = fields.Char(index=True, readonly=True, required=True)
    model_id = fields.Many2one(
        comodel_name='ir.model', string='Model',
        compute="_compute_model_id", store=True)

    @api.multi
    @api.depends("model")
    def _compute_model_id(self):
        for s in self:
            s.model_id = self.env["ir.model"].search([("model", "=", s.model)])

    def _get_move_line_act_window_dict(self):
        return self.env.ref('account.action_tax_code_line_open').read()[0]

    @api.multi
    def get_calculated_move_lines(self):
        res = self._get_move_line_act_window_dict()
        res['domain'] = [('id', 'in', self.move_lines.ids)]
        return res
