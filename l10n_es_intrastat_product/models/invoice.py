# -*- coding: utf-8 -*-
# © 2016 - FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    intrastat_transport = fields.Selection([
        (1, 'Transport maritime'),
        (2, 'Transport par chemin de fer'),
        (3, 'Transport par route'),
        (4, 'Transport par air'),
        (5, 'Envois postaux'),
        (7, 'Installations de transport fixes'),
        (8, 'Transport par navigation intérieure'),
        (9, 'Propulsion propre')
    ], string='Type of transport',
        help="Type of transport of the goods. This information is "
        "required for the product intrastat report (DEB).")
    intrastat_state = fields.Many2one(
        'res.country.state', string='State',
        help="For a customer invoice, contains Spain's state "
        "number from which the goods have be shipped. For a supplier "
        "invoice, contains Spain's state number of reception "
        "of the goods. This information is required for the product "
        "intrastat report.")
    intrastat_country_id = fields.Many2one(
        'res.country', string='Destination/Origin country of the goods',
        help="For a customer invoice, contains the country to which "
        "the goods have been shipped. For a supplier invoice, contains "
        "the country from which the goods have been shipped.")
    intrastat_type_id = fields.Many2one(
        'report.intrastat.type', string='Intrastat type', ondelete='restrict')
    incoterm_id = fields.Many2one('stock.incoterms', string='Incoterm')
