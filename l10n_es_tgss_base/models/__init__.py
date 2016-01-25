# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from . import (contribution_account,
               contribution_group,
               professional_category,
               study_level)
from .common import _NS
from openerp import models


class FullABC(models.AbstractModel):
    """Models inheriting this ABC will have all functionality bundled."""
    _name = "%s.full_abc" % _NS
    _inherit = [module.ABC._name for module in (contribution_account,
                                                contribution_group,
                                                professional_category,
                                                study_level)]
