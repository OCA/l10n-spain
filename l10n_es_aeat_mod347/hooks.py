# -*- coding: utf-8 -*-
# © 2014-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
#             (http://www.serviciosbaeza.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import SUPERUSER_ID


def post_init_hook(cr, registry):
    # Assign quarters on first time
    period_obj = registry['account.period']
    period_ids = period_obj.search(cr, SUPERUSER_ID, [])
    period_obj.assign_quarter(cr, SUPERUSER_ID, period_ids)
