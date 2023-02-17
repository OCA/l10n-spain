# -*- coding: utf-8 -*-
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2016-2017 Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tools import config
from odoo import _, api, exceptions, fields, models, registry


class L10nEsAeatReportTaxMapping(models.AbstractModel):
    _name = "l10n.es.aeat.report.tax.mapping"
    _inherit = "l10n.es.aeat.report"
    _description = ("Inheritable abstract model to add taxes by code mapping "
                    "in any AEAT report")

    tax_line_ids = fields.One2many(
        comodel_name='l10n.es.aeat.tax.line', inverse_name='res_id',
        domain=lambda self: [("model", "=", self._name)], auto_join=True,
        readonly=True, oldname='tax_lines', string="Tax lines")

    @api.multi
    def calculate(self):
        res = super(L10nEsAeatReportTaxMapping, self).calculate()
        tax_line_obj = self.env['l10n.es.aeat.tax.line']
        for report in self:
            report.tax_line_ids.unlink()
            # Buscar configuración de mapeo de impuestos
            tax_code_map = self.env['l10n.es.aeat.map.tax'].search(
                [('model', '=', report.number),
                 '|',
                 ('date_from', '<=', report.date_start),
                 ('date_from', '=', False),
                 '|',
                 ('date_to', '>=', report.date_end),
                 ('date_to', '=', False)], limit=1)
            if tax_code_map:
                # Due to a bug in ORM that unlinks other tables' records, we
                # have to avoid (0, 0, x) syntax
                # Reference: https://github.com/odoo/odoo/issues/18438
                for map_line in tax_code_map.map_line_ids:
                    map_line_vals = report._prepare_tax_line_vals(map_line)
                    map_line_vals.update({
                        'model': report._name,
                        'res_id': report.id,
                    })
                    tax_line_obj.create(map_line_vals)
                report.modified(['tax_line_ids'])
                report.recompute()
        return res

    @api.multi
    def unlink(self):
        self.mapped('tax_line_ids').unlink()
        return super(L10nEsAeatReportTaxMapping, self).unlink()

    @api.multi
    def _prepare_tax_line_vals(self, map_line):
        self.ensure_one()
        move_lines = self._get_tax_lines(
            map_line.mapped('tax_ids.description'),
            self.date_start, self.date_end, map_line,
        )
        credit = move_lines.get("credit", 0.0)
        debit = move_lines.get("debit", 0.0)
        move_line_ids = move_lines.get("ids", [])
        if map_line.sum_type == 'credit':
            amount = credit
        elif map_line.sum_type == 'debit':
            amount = debit
        else:  # map_line.sum_type == 'both'
            amount = credit - debit
        if map_line.inverse:
            amount = (-1.0) * amount
        return {
            'model': self._name,
            'res_id': self.id,
            'map_line_id': map_line.id,
            'amount': amount,
            'move_line_ids': [(6, 0, move_line_ids)],
        }

    @api.multi
    def _get_partner_domain(self):
        return []

    def get_taxes_from_map(self, map_line):
        return self.get_taxes_from_templates(map_line.tax_ids)

    @api.multi
    def _get_move_line_domain(self, codes, date_start, date_end, map_line):
        self.ensure_one()
        taxes = self.get_taxes_from_map(map_line)
        move_line_domain = [
            ('company_id', 'child_of', self.company_id.id),
            ('date', '>=', date_start),
            ('date', '<=', date_end)
        ]
        if map_line.move_type == 'regular':
            move_line_domain.append(
                ('move_id.move_type', 'in',
                 ('receivable', 'payable', 'liquidity'))
            )
        elif map_line.move_type == 'refund':
            move_line_domain.append(
                ('move_id.move_type', 'in', ('receivable_refund',
                                             'payable_refund')))
        if map_line.field_type == 'base':
            move_line_domain.append(('tax_ids', 'in', taxes.ids))
        elif map_line.field_type == 'amount':
            move_line_domain.append(('tax_line_id', 'in', taxes.ids))
        else:  # map_line.field_type == 'both'
            move_line_domain += [
                '|',
                ('tax_line_id', 'in', taxes.ids),
                ('tax_ids', 'in', taxes.ids)
            ]
        if map_line.sum_type == 'debit':
            move_line_domain.append(('debit', '>', 0))
        elif map_line.sum_type == 'credit':
            move_line_domain.append(('credit', '>', 0))
        if map_line.exigible_type == 'yes':
            move_line_domain.append(('tax_exigible', '=', True))
        elif map_line.exigible_type == 'no':
            move_line_domain.append(('tax_exigible', '=', False))
        move_line_domain += self._get_partner_domain()
        return move_line_domain

    def _get_tax_lines(self, codes, date_start, date_end, map_line):
        """Get the move lines for the codes and periods associated

        :param codes: List of strings for the tax codes
        :param date_start: Start date of the period
        :param date_stop: Stop date of the period
        :param map_line: Mapping line record
        :return: Dict with Move Line IDs, credit SUM and debit SUM.
        """
        domain = self._get_move_line_domain(
            codes, date_start, date_end, map_line,
        )
        ids = []
        credit = 0
        debit = 0
        search_fields = ["id", "credit", "debit"]
        limit = 100000
        offset = 0
        should_search = True
        while should_search:
            with api.Environment.manage():
                env = self.env
                if not config["test_enable"]:
                    new_cr = registry(self.env.cr.dbname).cursor()
                    env = api.Environment(new_cr, self._uid, self._context)
                lines = env['account.move.line'].with_context(
                    recompute=False,
                ).search_read(
                    domain=domain,
                    fields=search_fields,
                    offset=offset,
                    limit=limit,
                    order="id ASC",
                )
                if limit > len(lines):
                    should_search = False
                else:
                    offset += len(lines)
                for line in lines:
                    ids.append(line["id"])
                    credit += line["credit"]
                    debit += line["debit"]
                if not config["test_enable"]:
                    env.cr.close()
                    env.clear()
        return {
            "ids": ids,
            "credit": credit,
            "debit": debit,
        }

    @api.model
    def _prepare_regularization_move_line(self, account_group):
        return {
            'name': account_group['account_id'][1],
            'account_id': account_group['account_id'][0],
            'debit': account_group['credit'],
            'credit': account_group['debit'],
        }

    @api.multi
    def _process_tax_line_regularization(self, tax_lines):
        self.ensure_one()
        groups = self.env['account.move.line'].read_group(
            [('id', 'in', tax_lines.mapped('move_line_ids').ids)],
            ['debit', 'credit', 'account_id'],
            ['account_id'])
        lines = []
        for group in groups:
            balance = group['debit'] - group['credit']
            if balance:
                group['debit'] = balance if balance > 0 else 0
                group['credit'] = -balance if balance < 0 else 0
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
        lines = self._process_tax_line_regularization(
            self.tax_line_ids.filtered('to_regularize'))
        lines += self._prepare_regularization_extra_move_lines()
        # Write counterpart with the remaining
        debit = sum(x['debit'] for x in lines)
        credit = sum(x['credit'] for x in lines)
        lines.append(self._prepare_counterpart_move_line(
            self.counterpart_account_id, debit, credit))
        return lines

    @api.multi
    def create_regularization_move(self):
        self.ensure_one()
        if not self.counterpart_account_id or not self.journal_id:
            raise exceptions.Warning(
                _("You must fill both journal and counterpart account."))
        move_vals = self._prepare_move_vals()
        line_vals_list = self._prepare_regularization_move_lines()
        move_vals['line_ids'] = [(0, 0, x) for x in line_vals_list]
        self.move_id = self.env['account.move'].create(move_vals)
