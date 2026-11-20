# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    sii_exempt_cause = fields.Selection(
        selection_add=[
            (
                "E7",
                "[E7] Operación exenta según el artículo 90 del "
                "Decreto Legislativo 1/2025 (anteriormente listada como "
                "Art. 110 Ley 4/2012).",
            ),
            (
                "E8",
                "[E8] Exenta Otros / Operación exenta según la Ley 20/1991",
            ),
        ],
        ondelete={"E7": "set null", "E8": "set null"},
    )
    sii_art25_tipo_bien = fields.Selection(
        string="Tipo de bien Art. 25 (L32)",
        selection=[
            (
                "01",
                "[01] Bien inmueble",
            ),
            (
                "02",
                "[02] Bien mueble",
            ),
            (
                "03",
                "[03] Intangible — derechos de uso de propiedad "
                "industrial o intelectual",
            ),
            (
                "04",
                "[04] Intangible — derechos de uso de know-how no patentado",
            ),
            (
                "05",
                "[05] Intangible — concesiones administrativas",
            ),
        ],
        help="ATC Lista L32 (TipoBienArt25) para exención "
        "Art. 25 REF de bienes de inversión.",
    )
