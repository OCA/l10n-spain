# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    @api.depends(
        "l10n_es_simplified_invoice_sequence_id.number_next_actual",
        "l10n_es_simplified_invoice_sequence_id.prefix",
        "l10n_es_simplified_invoice_sequence_id.padding",
    )
    def _compute_simplified_invoice_sequence(self):
        for pos in self:
            seq = pos.l10n_es_simplified_invoice_sequence_id
            pos.l10n_es_simplified_invoice_number = (
                seq._get_current_sequence().number_next_actual
            )
            pos.l10n_es_simplified_invoice_prefix = seq._get_prefix_suffix()[0]
            pos.l10n_es_simplified_invoice_padding = seq.padding

    iface_l10n_es_simplified_invoice = fields.Boolean(
        string="Use simplified invoices for this POS",
    )
    is_simplified_config = fields.Boolean(
        store=False, compute="_compute_simplified_config"
    )
    l10n_es_simplified_invoice_sequence_id = fields.Many2one(
        "ir.sequence",
        string="Simplified Invoice IDs Sequence",
        help="Autogenerate for each POS created",
        copy=False,
        readonly=True,
    )
    l10n_es_simplified_invoice_limit = fields.Float(
        string="Sim.Inv limit amount",
        digits="Account",
        help="Over this amount is not legally posible to create "
        "a simplified invoice",
        default=3000,  # Spanish legal limit
    )
    l10n_es_simplified_invoice_prefix = fields.Char(
        "Simplified Invoice prefix",
        readonly=True,
        compute="_compute_simplified_invoice_sequence",
    )
    l10n_es_simplified_invoice_padding = fields.Integer(
        "Simplified Invoice padding",
        readonly=True,
        compute="_compute_simplified_invoice_sequence",
    )
    l10n_es_simplified_invoice_number = fields.Integer(
        "Sim.Inv number",
        readonly=True,
        compute="_compute_simplified_invoice_sequence",
    )

    @api.depends("iface_l10n_es_simplified_invoice")
    def _compute_simplified_config(self):
        for pos in self:
            pos.is_simplified_config = pos.iface_l10n_es_simplified_invoice

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Auto create simp. inv. sequence
            prefix = initial_prefix = "{}{}".format(
                vals["name"], self._get_default_prefix()
            )
            ith = 0
            while self.env["ir.sequence"].search_count([("prefix", "=", prefix)]):
                ith += 1
                prefix = "{}_{}".format(initial_prefix, ith)
            simp_inv_seq_id = self.env["ir.sequence"].create(
                {
                    "name": _("Simplified Invoice %s") % vals["name"],
                    "implementation": "standard",
                    "padding": self._get_default_padding(),
                    "prefix": prefix,
                    "code": "pos.config.simplified_invoice",
                    "company_id": vals.get("company_id", False),
                }
            )
            vals["l10n_es_simplified_invoice_sequence_id"] = simp_inv_seq_id.id
        return super().create(vals_list)

    @api.onchange("iface_l10n_es_simplified_invoice")
    def _onchange_l10n_iface_l10n_es_simplified_invoice(self):
        if self.iface_l10n_es_simplified_invoice and not self.invoice_journal_id:
            self.invoice_journal_id = self._default_invoice_journal()

    def copy(self, default=None):
        return super(
            PosConfig,
            self.with_context(copy_pos_config=True),
        ).copy(default)

    def write(self, vals):
        if not self._context.get("copy_pos_config") and "name" not in vals:
            for pos in self:
                sequence = pos.l10n_es_simplified_invoice_sequence_id
                sequence.check_simplified_invoice_unique_prefix()
        if "name" in vals:
            prefix = self.l10n_es_simplified_invoice_prefix.replace(
                self.name, vals["name"]
            )
            if prefix != self.l10n_es_simplified_invoice_prefix:
                self.l10n_es_simplified_invoice_sequence_id.update(
                    {
                        "prefix": prefix,
                        "name": (
                            self.l10n_es_simplified_invoice_sequence_id.name.replace(
                                self.name, vals["name"]
                            )
                        ),
                    }
                )
        return super().write(vals)

    def unlink(self):
        self.mapped("l10n_es_simplified_invoice_sequence_id").unlink()
        return super().unlink()

    def _get_default_padding(self):
        return self.env["ir.config_parameter"].get_param(
            "l10n_es_pos.simplified_invoice_sequence.padding", 4
        )

    def _get_default_prefix(self):
        return self.env["ir.config_parameter"].get_param(
            "l10n_es_pos.simplified_invoice_sequence.prefix", ""
        )

    def _get_l10n_es_sequence_name(self):
        """HACK: This is done for getting the proper translation."""
        return _("Simplified Invoice %s")
