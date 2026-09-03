# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_iface_l10n_es_simplified_invoice = fields.Boolean(
        related="pos_config_id.iface_l10n_es_simplified_invoice",
        readonly=False,
    )
    pos_l10n_es_simplified_invoice_sequence_id = fields.Many2one(
        related="pos_config_id.l10n_es_simplified_invoice_sequence_id",
    )
    pos_l10n_es_simplified_invoice_limit = fields.Float(
        related="pos_config_id.l10n_es_simplified_invoice_limit",
        readonly=False,
    )
    pos_l10n_es_simplified_invoice_prefix = fields.Char(
        related="pos_config_id.l10n_es_simplified_invoice_prefix",
    )
    pos_l10n_es_simplified_invoice_padding = fields.Integer(
        related="pos_config_id.l10n_es_simplified_invoice_padding",
    )
    pos_l10n_es_simplified_invoice_number = fields.Integer(
        related="pos_config_id.l10n_es_simplified_invoice_number",
    )
