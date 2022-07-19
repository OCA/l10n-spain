# Copyright (C) 2022 Trey, Kilobytes de Soluciones - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, models
from odoo.exceptions import ValidationError


class OpeningClosingXslx(models.AbstractModel):
    _name = 'report.o_c.report_opening_closing_xlsx'
    _inherit = 'report.account_financial_report.abstract_report_xlsx'

    def _get_report_name(self, report):
        if report.move_type == "opening":
            report_name = _('Opening Move')
        else:
            report_name = _('Closing Move')
        return self._get_report_complete_name(report, report_name)

    def _get_report_columns(self, report):
        return {
            0: {'header': _('Code'), 'field': 'code', 'width': 10},
            1: {'header': _('Account'), 'field': 'name', 'width': 60},
            2: {'header': _('Debit'),
                'field': 'initial_balance',
                'type': 'amount',
                'width': 14},
            3: {'header': _('Credit'),
                'field': 'final_balance',
                'type': 'amount',
                'width': 14},
        }

    def _get_report_filters(self, report):
        return []

    def _get_col_count_filter_name(self):
        return 2

    def _get_col_count_filter_value(self):
        return 2

    def _get_earning_account(self):
        account_type = self.env.ref('account.data_unaffected_earnings')
        return self.env['account.account'].search([
            ('user_type_id', '=', account_type.id),
            ('company_id', '=', self.env.user.company_id.id),
        ])

    def _generate_report_content(self, workbook, report):
        self.write_array_header()
        sum_debit = 0
        sum_credit = 0
        pos = 0
        account_id = self._get_earning_account()
        if len(account_id) != 1:
            raise ValidationError(
                _('Company must have a profit loss account.'))
        for account in report.account_ids.sorted(key='code', reverse=True):
            if (account.initial_balance and report.move_type == 'opening') or \
                    (account.final_balance and report.move_type == 'closing'):
                debit, credit, pos = self.write_line_opening_closing(account)
                sum_debit += debit
                sum_credit += credit
        if report.move_type == 'closing' and sum_debit - sum_credit:
            self.sheet.write_string(pos, 0, account_id.code)
            self.sheet.write_string(pos, 1, account_id.name)
            if sum_debit - sum_credit > 0:
                self.sheet.write_number(pos, 3, float(0), self.format_amount)
                self.sheet.write_number(
                    pos, 2, float(abs(sum_debit - sum_credit)),
                    self.format_amount)
            else:
                self.sheet.write_number(pos, 2, float(0), self.format_amount)
                self.sheet.write_number(
                    pos, 3, float(abs(sum_debit - sum_credit)),
                    self.format_amount)

    def write_line_opening_closing(self, line_object):
        move_type = line_object.report_id.move_type
        sum_debit = 0
        sum_credit = 0
        can_write = True
        for col_pos, column in self.columns.items():
            value = getattr(line_object, column['field'])
            cell_type = column.get('type', 'string')
            if cell_type == 'string':
                if move_type == 'closing' and \
                        line_object.code.startswith('129'):
                    can_write = False
                if line_object.code.startswith('6') or \
                        line_object.code.startswith('7'):
                    can_write = False
                if can_write:
                    self.sheet.write_string(self.row_pos, col_pos, value or '')
            elif cell_type == 'amount':
                cell_format = self.format_amount
                if move_type == 'opening':
                    if column['field'] == 'final_balance':
                        continue
                    if value > 0:
                        value = abs(value)
                        self.sheet.write_number(
                            self.row_pos, col_pos, float(value), cell_format
                        )
                        self.sheet.write_number(
                            self.row_pos, col_pos + 1, float(0), cell_format
                        )
                    else:
                        value = abs(value)
                        self.sheet.write_number(
                            self.row_pos, col_pos, float(0), cell_format
                        )
                        self.sheet.write_number(
                            self.row_pos, col_pos + 1, float(value), cell_format
                        )
                else:
                    if column['field'] == 'initial_balance':
                        continue
                    if value > 0:
                        value = abs(value)
                        if line_object.code.startswith('6') or \
                                line_object.code.startswith('7') or \
                                line_object.code.startswith('129'):
                            sum_credit += value
                            continue
                        if can_write:
                            self.sheet.write_number(
                                self.row_pos, col_pos, float(value), cell_format
                            )
                            self.sheet.write_number(
                                self.row_pos, col_pos - 1, float(0), cell_format
                            )
                    else:
                        value = abs(value)
                        if line_object.code.startswith('6') or \
                                line_object.code.startswith('7') or \
                                line_object.code.startswith('129'):
                            sum_debit += value
                            continue
                        if can_write:
                            self.sheet.write_number(
                                self.row_pos, col_pos, float(0), cell_format
                            )
                            self.sheet.write_number(
                                self.row_pos, col_pos - 1, float(value), cell_format
                            )
                can_write = True
        if can_write:
            self.row_pos += 1
        return sum_debit, sum_credit, self.row_pos
