# Copyright 2024 Aures TIC - Jose Zambudio <jose@aurestic.es>
# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    verifactu_enabled = fields.Boolean(
        related="company_id.verifactu_enabled",
        readonly=True,
    )
    verifactu_tax_key = fields.Selection(
        selection="_get_verifactu_tax_keys",
    )
    verifactu_registration_key = fields.Many2one(
        "aeat.verifactu.registration.keys",
        ondelete="restrict",
    )
    verifactu_active = fields.Boolean(
        copy=False,
        default=True,
        help="Enable Verifactu for this fiscal position?",
    )

    @api.model
    def default_verifactu_tax_key(self):
        return "01"

    @api.model
    def _get_verifactu_tax_keys(self):
        return [
            ("01", "Impuesto sobre el Valor Añadido (IVA)"),
            (
                "02",
                """Impuesto sobre la Producción, los Servicios y
                la Importación (IPSI) de Ceuta y Melilla""",
            ),
            ("03", "Impuesto General Indirecto Canario (IGIC)"),
            ("05", "Otros"),
        ]
