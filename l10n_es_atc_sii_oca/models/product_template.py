# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    sii_exempt_cause = fields.Selection(
        selection_add=[
            (
                "E1",
                "[E1] Operación exenta según el capítulo I del "
                "Decreto Legislativo 1/2025 (anteriormente listada como "
                "Art. 50 Ley 4/2012).",
            ),
            (
                "E2",
                "[E2] Operación exenta según el artículo 11 de la Ley 20/1991.",
            ),
            (
                "E3",
                "[E3] Operación exenta según el artículo 12 de la Ley 20/1991.",
            ),
            (
                "E4",
                "[E4] Operación exenta según el artículo 13 de la Ley 20/1991.",
            ),
            (
                "E5",
                "[E5] Operación exenta según el artículo 25 de la Ley 19/1994, "
                "de 6 de julio, del IGIC.",
            ),
            (
                "E6",
                "[E6] Operación exenta según el artículo 47 de la Ley 19/1994.",
            ),
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
                "[01] Obra sobre bien de inversión inmueble",
            ),
            (
                "02",
                "[02] Obra sobre bien de inversión mueble",
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
