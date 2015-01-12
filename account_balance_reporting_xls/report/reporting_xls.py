# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

import xlwt
from datetime import datetime
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import _render
from .reporting import account_balance_reporting_print
from openerp.tools.translate import _
# _ir_translation_name = 'reporting.xls'


class account_balance_reporting_xls_parser(account_balance_reporting_print):

    def __init__(self, cr, uid, name, context):
        super(account_balance_reporting_xls_parser,
              self).__init__(cr, uid, name, context=context)
        account_br_obj = self.pool.get('account.balance.reporting')
        self.context = context
        wanted_list = account_br_obj._report_xls_fields(cr, uid, context)
        template_changes = account_br_obj._report_xls_template(cr, uid,
                                                               context)
        self.localcontext.update({
            'datetime': datetime,
            'wanted_list': wanted_list,
            'template_changes': template_changes,
        })


class account_balance_reporting_xls(report_xls):

    def __init__(self, name, table,
                 rml=False, parser=False, header=True, store=False):
        super(account_balance_reporting_xls,
              self).__init__(name, table, rml, parser, header, store)

        # Cell Styles
        _xs = self.xls_styles
        # header
        rh_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rh_cell_style = xlwt.easyxf(rh_cell_format)
        self.rh_cell_style_center = xlwt.easyxf(rh_cell_format + _xs['center'])
        self.rh_cell_style_right = xlwt.easyxf(rh_cell_format + _xs['right'])
        # lines
        aml_cell_format = _xs['borders_all']
        self.aml_cell_style = xlwt.easyxf(aml_cell_format)
        self.aml_cell_style_center = xlwt.easyxf(
            aml_cell_format + _xs['center'])
        self.aml_cell_style_date = xlwt.easyxf(
            aml_cell_format + _xs['left'],
            num_format_str=report_xls.date_format)
        self.aml_cell_style_decimal = xlwt.easyxf(
            aml_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)
        # totals
        rt_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        self.rt_cell_style = xlwt.easyxf(rt_cell_format)
        self.rt_cell_style_right = xlwt.easyxf(rt_cell_format + _xs['right'])
        self.rt_cell_style_decimal = xlwt.easyxf(
            rt_cell_format + _xs['right'],
            num_format_str=report_xls.decimal_format)

        # XLS Template
        # [Cell columns span, cell width, content type, ??]
        self.col_specs_lines_template = {
            'name': {
                'header': [1, 80, 'text', _render("_('Concepto')")],
                'lines': [1, 0, 'text', _render("l['name']")],
                'totals': [1, 0, 'text', None],
            },
            'code': {
                'header': [1, 10, 'text', _render("_('Código')")],
                'lines': [1, 0, 'text', _render("l['code']")],
                'totals': [1, 0, 'text', None],
            },
            'previous_value': {
                'header': [1, 15, 'text', _render("_('Valor anterior')"),
                           None, self.rh_cell_style_right],
                'lines': [1, 0, 'number', _render("l['previous_value']"),
                          None, self.aml_cell_style_decimal],
                'totals': [1, 0, 'text', None]
            },
            'current_value': {
                'header': [1, 15, 'text', _render("_('Valor actual')"),
                           None, self.rh_cell_style_right],
                'lines': [1, 0, 'number', _render("l['current_value']"),
                          None, self.aml_cell_style_decimal],
                'totals': [1, 0, 'text', None]
            },
            'balance': {
                'header': [1, 15, 'text', _render("_('Balance')"),
                           None, self.rh_cell_style_right],
                'lines': [1, 0, 'number', _render("l['balance']"),
                          None, self.aml_cell_style_decimal],
                'totals': [1, 0, 'text', None]
            },
            'notes': {
                'header': [1, 30, 'text', _render("_('Notas')")],
                'lines': [1, 0, 'text', _render("l['notes']")],
                'totals': [1, 0, 'text', None],
            },
        }

    def generate_xls_report(self, _p, _xs, data, objects, wb):
        wanted_list = _p.wanted_list
        self.wanted_list = wanted_list
        self.col_specs_lines_template.update(_p.template_changes)

        sheet_name = _(_p.data['report_name'])
        ws = wb.add_sheet(sheet_name)
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0  # Landscape
        ws.fit_width_to_pages = 1
        row_pos = 0

        # set print header/footer
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']

        # Title
        r_n = _(_p.data['report_name'])
        t_n = _(_p.additional_data['tname'])
        c_d = _(_p.additional_data['calc_date'])
        report_name = (r_n + ' (' + t_n + ') - ' + c_d)
        cell_style = xlwt.easyxf(_xs['xls_title'])
        c_specs = [
            ('report_name', 6, 0, 'text', report_name),
        ]
        row_data = self.xls_row_template(c_specs, ['report_name'])
        row_pos = self.xls_write_row(ws, row_pos, row_data,
                                     row_style=cell_style)
        row_pos += 1

        # Column headers
        c_specs = map(lambda x: self.render(x, self.col_specs_lines_template,
                                            'header',
                                            render_space={'_': _p._}),
                      wanted_list)
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_pos = self.xls_write_row(ws, row_pos, row_data,
                                     row_style=self.rh_cell_style,
                                     set_column_size=True)
        ws.set_horz_split_pos(row_pos)

        for o in objects:
            for l in _p.lines(o):
                # Data
                cslt = self.col_specs_lines_template
                c_specs = map(lambda x: self.render(x, cslt, 'lines'),
                              wanted_list)
                row_data = self.xls_row_template(c_specs,
                                                 [x[0] for x in c_specs])
                row_pos = self.xls_write_row(ws, row_pos, row_data)

account_balance_reporting_xls('report.reporting.xls',
                              'account.balance.reporting',
                              parser=account_balance_reporting_xls_parser)
