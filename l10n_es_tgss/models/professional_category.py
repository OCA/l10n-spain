# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class ProfessionalCategory(models.Model):
    _description = "Spanish Social Security professional categories"
    _name = "l10n.es.tgss.professional_category"
    _inherit = "l10n.es.tgss.number_name"


class ABC(models.AbstractModel):
    _description = "Base for models linked to a professional category"
    _name = "l10n.es.tgss.professional_category.abc"

    professional_category_id = fields.Many2one(
        "l10n.es.tgss.professional_category",
        "Professional category",
        ondelete="restrict")
