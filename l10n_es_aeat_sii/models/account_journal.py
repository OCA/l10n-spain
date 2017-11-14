# -*- coding: utf-8 -*-
# Copyright 2017 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import osv, fields


class AccountJournal(osv.Model):
    _inherit = 'account.journal'

    _columns = {
        'sii_travel_tax_free': fields.boolean(
            string='Travel Tax Free', copy=False, default=False,
        ),

    }

    _defaults = {
                    'sii_travel_tax_free': False,
                }
