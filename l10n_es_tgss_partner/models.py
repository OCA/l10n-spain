# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models


class Partner(models.Model):
    _name = "res.partner"
    _inherit = [_name, "l10n_es_tgss_base.full_abc"]
