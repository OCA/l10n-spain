# Copyright 2026 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    verifactu_import_journal = fields.Boolean(
        string="External SIF invoice journal",
        help=(
            "Use this sales journal for invoices already issued by another SIF. "
            "Odoo will account for them without issuing or sending them again."
        ),
    )

    def _is_verifactu_exempt(self):
        return bool(self.verifactu_import_journal)

    def _check_external_journal_transition(self, vals):
        if "verifactu_import_journal" not in vals:
            return
        target = bool(vals["verifactu_import_journal"])
        changed = self.filtered(
            lambda journal: journal.verifactu_import_journal != target
        )
        if not changed:
            return
        if not target:
            raise ValidationError(
                _("An external SIF invoice journal cannot become a normal journal.")
            )
        if self.env["account.move"].search_count(
            [
                ("journal_id", "in", changed.ids),
                ("last_verifactu_invoice_entry_id", "!=", False),
            ]
        ):
            raise ValidationError(
                _(
                    "A journal that has generated VERI*FACTU entries cannot become "
                    "an external SIF invoice journal."
                )
            )

    @api.onchange("verifactu_import_journal")
    def _onchange_verifactu_import_journal(self):
        if self.verifactu_import_journal:
            self.verifactu_enabled = False

    @api.model_create_multi
    def create(self, vals_list):
        normalized_vals_list = []
        for vals in vals_list:
            vals = dict(vals)
            if vals.get("verifactu_import_journal"):
                vals["verifactu_enabled"] = False
            normalized_vals_list.append(vals)
        return super().create(normalized_vals_list)

    def write(self, vals):
        vals = dict(vals)
        self._check_external_journal_transition(vals)
        external = self.filtered(
            lambda journal: vals.get(
                "verifactu_import_journal", journal.verifactu_import_journal
            )
        )
        normal = self - external
        if external:
            super(AccountJournal, external).write(dict(vals, verifactu_enabled=False))
        if normal:
            super(AccountJournal, normal).write(vals)
        return True

    @api.constrains("type", "verifactu_import_journal")
    def _check_external_journal(self):
        if self.filtered(
            lambda journal: journal.verifactu_import_journal and journal.type != "sale"
        ):
            raise ValidationError(
                _("An external SIF invoice journal must be a sales journal.")
            )
