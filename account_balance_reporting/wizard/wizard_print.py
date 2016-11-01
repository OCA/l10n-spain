# -*- coding: utf-8 -*-
# Copyright 2009 Pexego Sistemas Informáticos.
# Copyright 2016 Vicent Cubells <vicent.cubells@tecnativa.com>
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class PrintWizard(models.TransientModel):
    _name = 'account.balance.reporting.print.wizard'

    @api.multi
    def _default_report_id(self):
        return self.env.context.get('active_id', False)

    @api.multi
    def _default_report_xml_id(self):
        report = self.env['account.balance.reporting'].browse(
            self._default_report_id())
        return report.template_id.report_xml_id.id

    report_id = fields.Many2one('account.balance.reporting', "Report",
                                default=_default_report_id)
    report_xml_id = fields.Many2one('ir.actions.report.xml', "Design",
                                    default=_default_report_xml_id)

    @api.multi
    def print_report(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': self.report_xml_id.report_name,
            'datas': {
                'ids': self.report_id.ids,
            }
        }
