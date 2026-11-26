# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class L10nEsSpfeRegistrationKey(models.Model):
    _name = "l10n.es.spfe.registration.key"
    _description = "SPFE Regime Key"
    _order = "tax_qualifier, code"

    code = fields.Char(size=2, required=True)
    name = fields.Char(string="Description", required=True, translate=True)
    tax_qualifier = fields.Selection(
        selection=[
            ("IVA", "IVA"),
            ("IGIC", "IGIC"),
            ("IPSI", "IPSI"),
        ],
        string="National Tax Qualifier",
        required=True,
        default="IVA",
    )
    active = fields.Boolean(default=True)

    @api.depends("code", "tax_qualifier", "name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = (
                f"[{record.tax_qualifier}-{record.code}] {record.name}"
            )

    @api.constrains("code", "tax_qualifier")
    def _check_unique_code_qualifier(self):
        for record in self:
            duplicate = self.search(
                [
                    ("id", "!=", record.id),
                    ("code", "=", record.code),
                    ("tax_qualifier", "=", record.tax_qualifier),
                ],
                limit=1,
            )
            if duplicate:
                raise ValidationError(
                    self.env._(
                        "SPFE regime key %(code)s already exists for %(qual)s.",
                        code=record.code,
                        qual=record.tax_qualifier,
                    )
                )
