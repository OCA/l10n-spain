# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models
from .. import exceptions as ex


class ABC(models.AbstractModel):
    _description = ("Base for models with special situations needed for "
                    "Spanish Social Security")
    _name = "l10n.es.tgss.special_situations.abc"

    affected_by_terrorism = fields.Boolean()
    affected_by_gender_violence = fields.Boolean()
    disability_percentage = fields.Integer()

    @api.multi
    @api.constrains("disability_percentage")
    def _disability_percentage_check(self):
        """Can only be a value from 0 to 100."""
        if self.filtered(lambda s: not 0 <= self.disability_percentage <= 100):
            raise ex.OutOfRangeError(percent=self.disability_percentage,
                                     name=self.display_name)
