# -*- coding: utf-8 -*-
# © 2016 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
try:
    import xlwt
except ImportError:
    xlwt = None
from datetime import datetime
from openerp.report import report_sxw
from openerp.tools.translate import translate, _

_ir_translation_name = 'account.invoice.export.xls'


class AccountInvoiceExportReportXlsParser(report_sxw.rml_parse):

    def set_context(self, objects, data, ids, report_type=None):
        super(AccountInvoiceExportReportXlsParser, self).set_context(
            objects, data, ids, report_type=report_type)
        self.invoice_type = data['invoice_type']
        self.company_id = data['company_id']
        self.period_ids = data['period_ids']

    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(AccountInvoiceExportReportXlsParser, self).__init__(
            cr, uid, name, context=context)
        invoice_pool = self.pool['account.invoice']
        wanted_list = invoice_pool._report_xls_fields(cr, uid, context)
        template_changes = invoice_pool._report_xls_template(cr, uid, context)
        self.localcontext.update({
            'datetime': datetime,
            'title': self._title,
            'wanted_list': wanted_list,
            'invoice_type': self._invoice_type,
            'template_changes': template_changes,
            'lines': self._lines,
            '_': self._
        })
        self.context = context

    def _(self, src):
        lang = self.context.get('lang', 'en_US')
        return translate(self.cr, _ir_translation_name, 'report', lang, src) \
            or src

    def _title(self):
        return self._(self.invoice_type)

    def _invoice_type(self):
        return self.invoice_type

    def _lines(self, object):
        additional_where = ""
        if self.period_ids:
            additional_where += self.cr.mogrify(
                "AND inv.period_id in %s", (tuple(self.period_ids),))
        sql = (
            "SELECT inv.date_invoice as date_invoice, "
            "inv.number as invoice_number, "
            "inv.supplier_invoice_number as supplier_invoice_number, "
            "cp.name as partner_name, cp.vat as partner_vat, "
            "coalesce(inv.cc_amount_untaxed, "
            "         inv.amount_untaxed) as amount_untaxed, "
            "coalesce(inv.cc_amount_total, "
            "         inv.amount_total) as amount_total, "
            "inv_tx.base as tax_line_base, "
            "inv_tx.name as tax_line_description, "
            "inv_tx.amount as tax_line_amount, "
            "inv_tx.base_amount as tax_line_base_amount, "
            "tx_cd.code as tax_line_base_tax_code, "
            "tx_cd.name as tax_line_base_tax_name, "
            "inv_tx.tax_amount as tax_line_tax_amount, "
            "tx_cd_t.code as tax_line_tax_tax_code, "
            "tx_cd_t.name as tax_line_tax_tax_name, "
            "mv.date as move_date "
            "FROM account_invoice inv "
            "INNER JOIN account_invoice_tax inv_tx "
            "    on inv_tx.invoice_id=inv.id "
            "LEFT JOIN account_tax_code tx_cd "
            "    on tx_cd.id=inv_tx.base_code_id "
            "LEFT JOIN account_tax_code tx_cd_t "
            "    on tx_cd_t.id=inv_tx.tax_code_id "
            "INNER JOIN account_move mv "
            "    on mv.id=inv.move_id "
            "INNER JOIN res_partner cp "
            "    on cp.id=mv.partner_id "
            "WHERE inv.move_id is not null "
            "    AND inv.type=%s"
            "    AND inv.company_id=%s"
            "    AND inv.state in ('open', 'paid') "
            " {} "
            " ORDER BY date_invoice ASC").format(additional_where)

        self.cr.execute(sql, (self.invoice_type, self.company_id))
        lines = self.cr.dictfetchall()
        return lines

try:
    from openerp.addons.report_xls.report_xls import report_xls
    from openerp.addons.report_xls.utils import _render

    class AccountInvoiceExportReportXls(report_xls):

        def __init__(self, name, table,
                     rml=False, parser=False, header=True, store=False):
            super(AccountInvoiceExportReportXls,
                  self).__init__(name, table, rml, parser, header, store)
            # Cell Styles
            _xs = self.xls_styles
            # header
            rh_cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
            self.rh_cell_style = xlwt.easyxf(rh_cell_format)
            self.rh_cell_style_center = xlwt.easyxf(
                rh_cell_format + _xs['center'])
            self.rh_cell_style_right = xlwt.easyxf(
                rh_cell_format + _xs['right'])
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
            self.rt_cell_style_right = xlwt.easyxf(rt_cell_format +
                                                   _xs['right'])
            self.rt_cell_style_decimal = xlwt.easyxf(
                rt_cell_format + _xs['right'],
                num_format_str=report_xls.decimal_format)

        def _prepare_col_spec_lines_template(self, invoice_type=None):
            # This is needed for translate tool to catch correctly lang handled
            user = self.pool['res.users'].browse(self.cr, self.uid, self.uid)
            context = {}
            context.update({'lang': user.lang})
            # XLS Template
            # [Cell columns span, cell width, content type, ??]
            spec_lines_template = {
                'date_invoice': {
                    'header': [1, 13, 'text', _('Date')],
                    'lines': [1, 0, 'date', _render(
                        "datetime.strptime(l['date_invoice'], '%Y-%m-%d')"),
                        None,
                        self.aml_cell_style_date],
                    'totals': [1, 0, 'text', None],
                },
                'move_date': {
                    'header': [1, 13, 'text', _('Account Move Date')],
                    'lines': [1, 0, 'date', _render(
                        "datetime.strptime(l['move_date'], '%Y-%m-%d')"),
                        None,
                        self.aml_cell_style_date],
                    'totals': [1, 0, 'text', None]
                },
                'invoice_number': {
                    'header': [1, 13, 'text', _('Number')],
                    'lines': [1, 0, 'text', _render("l['invoice_number']")],
                    'totals': [1, 0, 'text', None]
                },
                'partner_name': {
                    'header': [1, 20, 'text', _('Partner Name')],
                    'lines': [1, 0, 'text', _render("l['partner_name']")],
                    'totals': [1, 0, 'text', None]
                },
                'partner_vat': {
                    'header': [1, 15, 'text', _('Partner Vat')],
                    'lines': [1, 0, 'text', _render("l['partner_vat']")],
                    'totals': [1, 0, 'text', None]
                },
                'amount_untaxed': {
                    'header': [1, 10, 'text', _('Amount Untaxed')],
                    'lines': [1, 0, 'number', _render("l['amount_untaxed']"),
                              None,
                              self.aml_cell_style_decimal],
                    'totals': [1, 0, 'text', None]
                },
                'amount_total': {
                    'header': [1, 10, 'text', _('Amount Total')],
                    'lines': [1, 0, 'number', _render("l['amount_total']"),
                              None,
                              self.aml_cell_style_decimal],
                    'totals': [1, 0, 'text', None]
                },
                'tax_line_base': {
                    'header': [1, 10, 'text', _('Tax Line Base')],
                    'lines': [1, 0, 'number', _render("l['tax_line_base']"),
                              None,
                              self.aml_cell_style_decimal],
                    'totals': [1, 0, 'text', None]
                },
                'tax_line_description': {
                    'header': [1, 25, 'text', _('Tax Line Description')],
                    'lines': [1, 0, 'text',
                              _render("l['tax_line_description']")],
                    'totals': [1, 0, 'text', None]
                },
                'tax_line_amount': {
                    'header': [1, 10, 'text', _('Tax Line Amount')],
                    'lines': [1, 0, 'number', _render("l['tax_line_amount']"),
                              None,
                              self.aml_cell_style_decimal],
                    'totals': [1, 0, 'text', None]
                },
                'tax_line_base_amount': {
                    'header': [1, 10, 'text', _('Tax Line Base Amount')],
                    'lines': [1, 0, 'number',
                              _render("l['tax_line_base_amount']"),
                              None,
                              self.aml_cell_style_decimal],
                    'totals': [1, 0, 'text', None]
                },
                'tax_line_base_tax_code': {
                    'header': [1, 10, 'text', _('Tax Line Base Tax Code')],
                    'lines': [1, 0, 'text',
                              _render("l['tax_line_base_tax_code']")],
                    'totals': [1, 0, 'text', None]
                },
                'tax_line_base_tax_name': {
                    'header': [1, 25, 'text', _('Tax Line Base Tax Name')],
                    'lines': [1, 0, 'text',
                              _render("l['tax_line_base_tax_name']")],
                    'totals': [1, 0, 'text', None]
                },
                'tax_line_tax_amount': {
                    'header': [1, 10, 'text', _('Tax Line Tax Amount')],
                    'lines': [1, 0, 'number',
                              _render("l['tax_line_tax_amount']"),
                              None,
                              self.aml_cell_style_decimal],
                    'totals': [1, 0, 'text', None]
                },
                'tax_line_tax_tax_code': {
                    'header': [1, 10, 'text', _('Tax Line Tax Code')],
                    'lines': [1, 0, 'text',
                              _render("l['tax_line_tax_tax_code']")],
                    'totals': [1, 0, 'text', None]
                },
                'tax_line_tax_tax_name': {
                    'header': [1, 25, 'text', _('Tax Line Tax Name')],
                    'lines': [1, 0, 'text',
                              _render("l['tax_line_tax_tax_name']")],
                    'totals': [1, 0, 'text', None]
                }
            }
            if invoice_type == 'in_invoice':
                spec_lines_template.update({
                    'invoice_number': {
                        'header': [1, 13, 'text', _('Number')],
                        'lines': [1, 0, 'text', _render(
                            "l['supplier_invoice_number'] "
                            "or l['invoice_number']")],
                        'totals': [1, 0, 'text', None]
                    }
                })
            return spec_lines_template

        def get_new_ws(self, _p, _xs, sheet_name, wb):
            wanted_list = _p.wanted_list
            self.wanted_list = wanted_list

            title = _p.title()
            report_name = title
            ws = wb.add_sheet(sheet_name)
            ws.panes_frozen = True
            ws.remove_splits = True
            ws.portrait = 0  # Landscape
            ws.fit_width_to_pages = 1
            # set print header/footer
            ws.header_str = self.xls_headers['standard']
            ws.footer_str = self.xls_footers['standard']
            row_pos = 0
            # Title
            cell_style = xlwt.easyxf(_xs['xls_title'])
            c_specs = [
                ('report_name', 1, 0, 'text', report_name),
            ]
            row_data = self.xls_row_template(c_specs, ['report_name'])
            row_pos = self.xls_write_row(ws, row_pos, row_data,
                                         row_style=cell_style)
            row_pos += 1
            # Column headers
            c_specs = map(lambda x: self.render(
                x, self.col_specs_lines_template, 'header',
                render_space={'_': _p._}), wanted_list)
            row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
            row_pos = self.xls_write_row(
                ws, row_pos, row_data, row_style=self.rh_cell_style,
                set_column_size=True)
            ws.set_horz_split_pos(row_pos)
            return ws, row_pos

        def generate_xls_report(self, _p, _xs, data, objects, wb):
            wanted_list = _p.wanted_list
            self.wanted_list = wanted_list
            self.col_specs_lines_template = \
                self._prepare_col_spec_lines_template(
                    invoice_type=_p.invoice_type())
            self.col_specs_lines_template.update(_p.template_changes)
            title = _p.title()
            sheet_name = title[:31]
            ws, row_pos = self.get_new_ws(_p, _xs, sheet_name, wb)

            ws_count = 0
            for o in objects:
                for l in _p.lines(o):
                    if row_pos >= 65536:
                        ws_count += 1
                        new_sheet_name = "%s_%s" % (sheet_name, ws_count)
                        ws, row_pos = self.get_new_ws(_p, _xs, new_sheet_name,
                                                      wb)
                    # Data
                    cslt = self.col_specs_lines_template
                    c_specs = map(lambda x: self.render(x, cslt, 'lines'),
                                  wanted_list)
                    row_data = self.xls_row_template(c_specs,
                                                     [x[0] for x in c_specs])
                    row_pos = self.xls_write_row(ws, row_pos, row_data)

    AccountInvoiceExportReportXls(
        'report.account.invoice.export.xls', 'xls.invoice.report.wizard',
        parser=AccountInvoiceExportReportXlsParser)

except ImportError:
    pass
