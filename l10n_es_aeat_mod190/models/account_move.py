# Copyright 2020 Creu Blanca
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    aeat_perception_key_id = fields.Many2one(
        comodel_name="l10n.es.aeat.report.perception.key",
        compute="_compute_aeat_perception_key_id",
        store=True,
        string="Clave percepción",
        help="Se consignará la clave alfabética que corresponda a las "
        "percepciones de que se trate.",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    aeat_perception_subkey_id = fields.Many2one(
        comodel_name="l10n.es.aeat.report.perception.subkey",
        compute="_compute_aeat_perception_subkey_id",
        store=True,
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
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    @api.depends("fiscal_position_id")
    def _compute_aeat_perception_key_id(self):
        for item in self.filtered(lambda x: x.fiscal_position_id):
            item.aeat_perception_key_id = item.fiscal_position_id.aeat_perception_key_id

    @api.depends("fiscal_position_id")
    def _compute_aeat_perception_subkey_id(self):
        for item in self.filtered(lambda x: x.fiscal_position_id):
            item.aeat_perception_subkey_id = (
                item.fiscal_position_id.aeat_perception_subkey_id
            )
