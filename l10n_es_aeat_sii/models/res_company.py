# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.osv import osv, fields


class ResCompany(osv.Model):
    _inherit = 'res.company'

    _columns = {
        'sii_test': fields.boolean(string='Test Enviroment'),
        'sii_enabled': fields.boolean(string='Enable SII'),
        'chart_template_id': fields.many2one('account.chart.template', 'Chart Template',
                                             required=True),
        'sii_method': fields.selection(
            string='Method',
            selection=[('auto', 'Automatic'), ('manual', 'Manual')],
            help='By default the invoice send in validate process, with manual '
                 'method, there a button to send the invoice.'),

        'sii_description_method': fields.selection(
            string='SII Description Method',
            selection=[('auto', 'Automatic'), ('fixed', 'Fixed'),
                       ('manual', 'Manual')],
            help="Method for the SII invoices description, can be one of these:\n"
                 "- Automatic: the description will be the join of the invoice "
                 "  lines description\n"
                 "- Fixed: the description write on the below field 'SII "
                 "  Description'\n"
                 "- Manual (by default): It will be necessary to manually enter "
                 "  the description on each invoice\n\n"
                 "For all the options you can append a header text using the "
                 "below fields 'SII Sale header' and 'SII Purchase header'"),
        'sii_description': fields.char(
            string="SII Description",
            help="The description for invoices. Only when the filed SII "
                 "Description Method is 'fixed'.",size=250),
        'sii_header_customer': fields.char(
            string="SII Customer header",
            help="An optional header description for customer invoices. "
                 "Applied on all the SII description methods",size=128),
        'sii_header_supplier': fields.char(
            string="SII Supplier header",
            help="An optional header description for supplier invoices. "
                 "Applied on all the SII description methods",size=128),

    }

    _defaults = {
        'sii_method': 'auto',
        'sii_description_method': 'manual'
    }
