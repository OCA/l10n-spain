# Copyright 2019 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnuorg/licenses/agpl.html).

import json

from odoo.addons.report_xlsx.controllers.main import ReportController
from odoo.http import content_disposition, route, request


class ReportController(ReportController):

    @route([
        '/report/xlsx/l10n_es_vat_book.<reportname>',
        '/report/xlsx/l10n_es_vat_book.<reportname>/<docids>',
    ], type='http', auth='user', website=True)
    def report_routes(self, reportname, docids=None, **data):
        reportname = 'l10n_es_vat_book.'+reportname
        converter = 'xlsx'
        report = request.env['ir.actions.report']._get_report_from_name(
            reportname)

        context = dict(request.env.context)
        report_file = False
        if docids:
            docids = [int(i) for i in docids.split(',')]
            vat_book = request.env['l10n.es.vat.book'].browse(
                docids)
            if reportname == 'l10n_es_vat_book.l10n_es_vat_book_issued_xlsx':
                report_file = vat_book._get_printed_report_name('E')
            if reportname == 'l10n_es_vat_book.l10n_es_vat_book_received_xlsx':
                report_file = vat_book._get_printed_report_name('R')
        if data.get('options'):
            data.update(json.loads(data.pop('options')))
        if data.get('context'):
            data['context'] = json.loads(data['context'])
            if data['context'].get('lang'):
                del data['context']['lang']
            context.update(data['context'])
        context['report_name'] = reportname

        xlsx = report.with_context(context).render_xlsx(
            docids, data=data
        )[0]
        if not report_file:
            report_file = reportname
        xlsxhttpheaders = [
            ('Content-Type', 'application/vnd.openxmlformats-'
                             'officedocument.spreadsheetml.sheet'),
            ('Content-Length', len(xlsx)),
            (
                'Content-Disposition',
                content_disposition(report_file + '.xlsx')
            )
        ]
        return request.make_response(xlsx, headers=xlsxhttpheaders)
