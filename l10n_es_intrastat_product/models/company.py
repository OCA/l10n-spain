# -*- coding: utf-8 -*-
# © 2016 - FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    default_intrastat_state = fields.Many2one(
        'res.country.state',
        string='Default departement code',
        help='If the Departement code is not set on the invoice, '
        'Odoo will use this value.')
    default_intrastat_transport = fields.Many2one(
        'intrastat.transport_mode',
        string='Default type of transport',
        help="If the 'Type of Transport' is not set on the invoice, "
        "OpenERP will use this value.")
    default_intrastat_type_out_invoice = fields.Many2one(
        'report.intrastat.type',
        string='Default intrastat type for customer invoice',
        ondelete='restrict')
    default_intrastat_type_out_refund = fields.Many2one(
        'report.intrastat.type',
        string='Default intrastat type for customer refund',
        ondelete='restrict')
    default_intrastat_type_in_invoice = fields.Many2one(
        'report.intrastat.type',
        string='Default intrastat type for supplier invoice',
        ondelete='restrict')
    default_intrastat_type_in_refund = fields.Many2one(
        'report.intrastat.type',
        string='Default intrastat type for supplier refund',
        ondelete='restrict')
    default_incoterm = fields.Many2one(
        'stock.incoterms',
        string='Default Incoterm')
