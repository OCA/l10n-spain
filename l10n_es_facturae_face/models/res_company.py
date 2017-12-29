# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class ResCompany(models.Model):
    _inherit = 'res.company'

    face_email = fields.Char()

    @api.constrains('face_email')
    def check_face_email(self):
        for record in self:
            if not re.match(
                    '(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$)',
                    record.face_email):
                raise ValidationError(_('Invalid facturae email'))
