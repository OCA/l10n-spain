# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    aeat_perception_key_id = fields.Many2one(
        comodel_name="l10n.es.aeat.report.perception.key",
        string="Clave percepción",
        help="Se consignará la clave alfabética que corresponda a las "
        "percepciones de que se trate.",
        compute="_compute_aeat_perception_keys",
        store=True,
    )
    aeat_perception_subkey_id = fields.Many2one(
        comodel_name="l10n.es.aeat.report.perception.subkey",
        string="Subclave",
        help="""Tratándose de percepciones correspondientes a las claves
                    B, E, F, G, H, I, K y L, deberá consignarse, además, la
                    subclave numérica de dos dígitos que corresponda a las
                    percepciones de que se trate, según la relación de
                    subclaves que para cada una de las mencionadas claves
                    figura a continuación.
                    En percepciones correspondientes a claves distintas de las
                    mencionadas, no se cumplimentará este campo.
                    Cuando deban consignarse en el modelo 190
                    percepciones satisfechas a un mismo perceptor que
                    correspondan a diferentes claves o subclaves de
                    percepción, deberán cumplimentarle tantos apuntes o
                    registros de percepción como sea necesario, de forma que
                    cada uno de ellos refleje exclusivamente los datos de
                    percepciones correspondientes a una misma clave y, en
                    su caso, subclave.""",
        compute="_compute_aeat_perception_keys",
        store=True,
    )

    @api.depends("move_id.aeat_perception_key_id")
    def _compute_aeat_perception_keys(self):
        for line in self:
            aeat_perception_key_id = False
            aeat_perception_subkey_id = False
            if (
                line.move_id.is_invoice()
                and not line.exclude_from_invoice_tab
                and line.id in line.move_id.invoice_line_ids.ids
                and line.move_id.aeat_perception_key_id
            ):
                aeat_perception_key_id = line.move_id.aeat_perception_key_id.id
                aeat_perception_subkey_id = line.move_id.aeat_perception_subkey_id.id
            line.update(
                {
                    "aeat_perception_key_id": aeat_perception_key_id,
                    "aeat_perception_subkey_id": aeat_perception_subkey_id,
                }
            )
