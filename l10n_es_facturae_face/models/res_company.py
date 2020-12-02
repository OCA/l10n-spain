# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    face_email = fields.Char()

    @api.constrains("face_email")
    def check_face_email(self):
        for record in self:
            if record.face_email and not re.match(
                "(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$)",
                record.face_email,
            ):
                raise ValidationError(_("Invalid facturae email"))
