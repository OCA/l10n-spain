# -*- coding: utf-8 -*-
# Copyright 2017 MINORISA (http://www.minorisa.net)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    sii_exempt_cause = fields.Selection(
        string="SII Exempt Cause",
        selection=[('none', 'None'),
                   ('E1', '[E1] Art. 20: Operaciones interiores exentas'),
                   ('E2', '[E2] Art. 21: Exenciones en las exportaciones de '
                          'bienes'),
                   ('E3', '[E3] Art. 22: Exenciones en las operaciones '
                          'asimiladas a las exportaciones'),
                   ('E4', '[E4] Art. 23 y 24: Exenciones relativas a '
                          'regímenes aduaneros y fiscales. Exenciones zonas '
                          'francas, depósitos francos y otros depósitos.'),
                   ('E5', '[E5] Art. 25: Exenciones en las entregas de bienes '
                          'destinados a otro estado miembro.'),
                   ('E6', '[E6] Otros')],
        default='none')
