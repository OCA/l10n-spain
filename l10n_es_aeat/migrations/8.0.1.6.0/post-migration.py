# -*- coding: utf-8 -*-
# © 2016 Antiun Ingenieria S.L. - Antonio Espinosa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from openerp import SUPERUSER_ID
from openerp.api import Environment


def migrate(cr, version):
    env = Environment(cr, SUPERUSER_ID, {})
    sequences = env['ir.sequence'].search([
        ('code', '=', 'aeat.sequence.type'),
    ])
    for seq in sequences:
        seq.prefix = re.sub(r'-', '', seq.prefix)
        seq.padding = 13 - len(seq.prefix)
