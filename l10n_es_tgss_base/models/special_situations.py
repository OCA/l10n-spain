# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models
from .common import _NS
from .. import exceptions as ex


class ABC(models.AbstractModel):
    """Models inheriting this ABC will have special situation details.

    These situations usually have impact in some TGSS transactions or
    indemnifications.
    """
    _name = "%s.special_situations_abc" % _NS

    affected_by_terrorism = fields.Boolean()
    affected_by_gender_violence = fields.Boolean()
    disability_percentage = fields.Integer()

    @api.one
    @api.constrains("disability_percentage")
    def _disability_percentage_check(self):
        """Can only be a value from 0 to 100."""
        if self.disability_percentage:
            if not 0 <= self.disability_percentage <= 100:
                raise ex.OutOfRangeError(self)
