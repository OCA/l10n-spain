# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

SPFE_WITHHOLDING_TYPES = [
    ("01", "[01] Art. 75.1.c) 1º RIRPF - Actividades profesionales"),
    ("02", "[02] Art. 75.1.c) 2º RIRPF - Actividades agrícolas y ganaderas"),
    ("03", "[03] Art. 75.1.c) 3º RIRPF - Actividades forestales"),
    ("04", "[04] Art. 75.1.c) 4º RIRPF - Actividades empresariales (módulos)"),
    ("05", "[05] Art. 75.1.d) 2º RIRPF - Aprovechamientos forestales"),
    ("06", "[06] Art. 75.2.a) RIRPF - Arrendamientos de inmuebles urbanos"),
    ("07", "[07] Art. 75.2.b) RIRPF - Propiedad intelectual/industrial/otros"),
    ("08", "[08] Art. 60.1.c) RIS - Administradores y consejeros"),
    ("09", "[09] Art. 60.1.d) RIS - Cesión derecho de imagen"),
    ("10", "[10] Art. 60.1.e) RIS - Arrendamiento inmuebles urbanos (IS)"),
    ("11", "[11] Otros"),
]


class AccountTax(models.Model):
    _inherit = "account.tax"

    spfe_is_surcharge = fields.Boolean(
        string="SPFE Equivalence Surcharge (RE)",
        help="Mark if this tax represents Spanish Equivalence Surcharge (Recargo "
        "de Equivalencia, category N in SPFE).",
    )
    spfe_is_withholding = fields.Boolean(
        string="SPFE Withholding Tax (IRPF/IS)",
        help="Mark if this tax represents a withholding tax reported in "
        "WithholdingTaxTotal and CollectionInvoiceLine (RETE).",
    )
    spfe_withholding_type = fields.Selection(
        selection=SPFE_WITHHOLDING_TYPES,
        string="SPFE Withholding Concept",
        default="01",
        help="Lista L5: Withholding tax concept reported in WithholdingTaxTotal.",
    )
    spfe_registration_key_id = fields.Many2one(
        comodel_name="l10n.es.spfe.registration.key",
        string="SPFE Regime Key",
        help="Default SPFE regime key (REGI) associated with this tax.",
    )
