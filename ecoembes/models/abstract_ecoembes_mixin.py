# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AbstractEcoembesMixin(models.AbstractModel):
    _name = "abstract.ecoembes.mixin"
    _description = "Abstract Ecoembes Mixin"

    name = fields.Char(string="Name", required=True)
    reference = fields.Char(string="Ref.", required=True)

    @api.constrains("reference")
    def _check_reference(self):
        for item in self:
            if not item.reference.isdigit():
                raise ValidationError(
                    _("Field 'reference' must have only digit characters")
                )

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([("reference", "ilike", name)] + args, limit=limit)
        if not recs:
            recs = self.search([("name", operator, name)] + args, limit=limit)
        return recs.name_get()
