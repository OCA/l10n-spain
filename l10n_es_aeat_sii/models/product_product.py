# -*- encoding: utf-8 -*-
# Copyright 2017 MINORISA (http://www.minorisa.net)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from osv import osv, fields


class product_template(osv.osv):
    _inherit = "product.template"

    _columns = {
        'sii_exempt_cause': fields.selection([('none', 'None'),
                   ('E1', 'E1'),
                   ('E2', 'E2'),
                   ('E3', 'E3'),
                   ('E4', 'E4'),
                   ('E5', 'E5'),
                   ('E6', 'E6')],'SII Exempt Cause'),
    }


    _defaults = {
        'sii_exempt_cause': 'none'
    }