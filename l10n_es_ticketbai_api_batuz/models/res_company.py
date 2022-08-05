# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Digital5, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models

from .lroe_operation import LROEModelEnum


class ResCompany(models.Model):
    _inherit = "res.company"

    lroe_model = fields.Selection(
        [
            (LROEModelEnum.model_pj_240.value, "LROE PJ 240"),
            (LROEModelEnum.model_pf_140.value, "LROE PF 140"),
        ],
        string="LROE Model",
        required=True,
        default=LROEModelEnum.model_pj_240.value,
    )
    main_activity_iae = fields.Char(
        string="Epígrafe I.A.E. actividad principal",
        size=7,
    )
