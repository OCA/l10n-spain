# Copyright 2014-2023 Binhex - Nicolás Ramos (http://binhex.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, api, fields, models

KEY_TAX_MAPPING = {
    "A": "l10n_es_atc_mod415.atc_mod415_map_a",
    "B": "l10n_es_atc_mod415.atc_mod415_map_b",
}


class L10nEsAtcMod415Report(models.Model):
    _inherit = "l10n.es.aeat.mod347.report"
    _name = "l10n.es.atc.mod415.report"
    _description = "ATC 415 Report"
    _period_yearly = True
    _period_quarterly = False
    _period_monthly = False
    _aeat_number = "415"

    number = fields.Char(default="415")
    partner_record_ids = fields.One2many(
        comodel_name="l10n.es.atc.mod415.partner_record",
        inverse_name="report_id",
        string="Partner Records",
    )
    real_estate_record_ids = fields.One2many(
        comodel_name="l10n.es.atc.mod415.real_estate_record",
        inverse_name="report_id",
        string="Real Estate Records",
    )

    def btn_list_records(self):
        return {
            "domain": "[('report_id','in'," + str(self.ids) + ")]",
            "name": _("Partner records"),
            "view_mode": "tree,form",
            "res_model": "l10n.es.atc.mod415.partner_record",
            "type": "ir.actions.act_window",
        }

    def _account_move_line_domain(self, taxes):
        """Return domain for searching move lines.

        :param: taxes: Taxes to look for in move lines.
        """
        return [
            ("partner_id.not_in_mod415", "=", False),
            ("move_id.not_in_mod415", "=", False),
            ("date", ">=", self.date_start),
            ("date", "<=", self.date_end),
            "|",
            ("tax_ids", "in", taxes.ids),
            ("tax_line_id", "in", taxes.ids),
            ("parent_state", "=", "posted"),
        ]

    def _create_partner_records(self, key, map_ref, partner_record=None):
        sign = -1 if key == "B" else 1
        partner_record_obj = self.env["l10n.es.atc.mod415.partner_record"]
        partner_obj = self.env["res.partner"]
        map_line = self.env.ref(map_ref)
        taxes = self._get_taxes(map_line)
        domain = self._account_move_line_domain(taxes)
        if partner_record:
            domain += [("partner_id", "=", partner_record.partner_id.id)]
        groups = self.env["account.move.line"].read_group(
            domain,
            ["partner_id", "balance"],
            ["partner_id"],
        )
        filtered_groups = list(
            filter(lambda d: abs(d["balance"]) > self.operations_limit, groups)
        )
        for group in filtered_groups:
            partner = partner_obj.browse(group["partner_id"][0])
            vals = {
                "report_id": self.id,
                "partner_id": partner.id,
                "representative_vat": "",
                "operation_key": key,
                "amount": sign * group["balance"],
            }
            vals.update(self._get_partner_347_identification(partner))
            move_groups = self.env["account.move.line"].read_group(
                group["__domain"],
                ["move_id", "balance"],
                ["move_id"],
            )
            vals["move_record_ids"] = [
                (
                    0,
                    0,
                    {
                        "move_id": move_group["move_id"][0],
                        "amount": sign * move_group["balance"],
                    },
                )
                for move_group in move_groups
            ]
            if partner_record:
                vals["move_record_ids"][0:0] = [
                    (2, x) for x in partner_record.move_record_ids.ids
                ]
                partner_record.write(vals)
            else:
                partner_record_obj.create(vals)

    def _create_cash_moves(self):
        partner_obj = self.env["res.partner"]
        move_line_obj = self.env["account.move.line"]
        cash_journals = self.env["account.journal"].search(
            [("type", "=", "cash")],
        )
        if not cash_journals:
            return
        domain = [
            ("account_id.account_type", "=", "asset_receivable"),
            ("journal_id", "in", cash_journals.ids),
            ("date", ">=", self.date_start),
            ("date", "<=", self.date_end),
            ("partner_id.not_in_mod415", "=", False),
        ]
        cash_groups = move_line_obj.read_group(
            domain, ["partner_id", "balance"], ["partner_id"]
        )
        for cash_group in cash_groups:
            partner = partner_obj.browse(cash_group["partner_id"][0])
            partner_record_obj = self.env["l10n.es.atc.mod415.partner_record"]
            amount = abs(cash_group["balance"])
            if amount > self.received_cash_limit:
                move_lines = move_line_obj.search(cash_group["__domain"])
                partner_record = partner_record_obj.search(
                    [
                        ("partner_id", "=", partner.id),
                        ("operation_key", "=", "B"),
                        ("report_id", "=", self.id),
                    ]
                )
                if partner_record:
                    partner_record.write(
                        {
                            "cash_record_ids": [(6, 0, move_lines.ids)],
                            "cash_amount": amount,
                        }
                    )
                else:
                    vals = {
                        "report_id": self.id,
                        "partner_id": partner.id,
                        "representative_vat": "",
                        "operation_key": "B",
                        "amount": 0,
                        "cash_amount": amount,
                        "cash_record_ids": [(6, 0, move_lines.ids)],
                    }
                    vals.update(self._get_partner_347_identification(partner))
                    partner_record_obj.create(vals)

    def calculate(self):
        for report in self:
            # Delete previous partner records
            report.partner_record_ids.unlink()
            with self.env.norecompute():
                self._create_partner_records("A", KEY_TAX_MAPPING["A"])
                self._create_partner_records("B", KEY_TAX_MAPPING["B"])
                self._create_cash_moves()
            self.flush_model()
            report.partner_record_ids.calculate_quarter_totals()
        return True


class L10nEsAtcMod415PartnerRecord(models.Model):
    _inherit = "l10n.es.aeat.mod347.partner_record"
    _name = "l10n.es.atc.mod415.partner_record"
    _description = "Partner Record"
    _rec_name = "partner_vat"
    _order = "check_ok asc,id"

    @api.model
    def _default_record_id(self):
        return self.env.context.get("report_id", False)

    report_id = fields.Many2one(
        comodel_name="l10n.es.atc.mod415.report",
        string="Modelo 415",
        ondelete="cascade",
        default=_default_record_id,
    )
    move_record_ids = fields.One2many(
        comodel_name="l10n.es.atc.mod415.move.record",
        inverse_name="partner_record_id",
        string="Move records",
    )

    @api.model
    def _get_partner_report_email_template(self):
        return self.env.ref("l10n_es_atc_mod415.email_template_415")

    def button_print(self):
        return self.env.ref("l10n_es_atc_mod415.415_partner").report_action(self)


class L10nEsAtcMod415RealStateRecord(models.Model):
    _inherit = "l10n.es.aeat.mod347.real_estate_record"
    _name = "l10n.es.atc.mod415.real_estate_record"
    _description = "Real Estate Record"
    _rec_name = "reference"
    _order = "check_ok asc,id"

    @api.model
    def _default_record_id(self):
        return self.env.context.get("report_id", False)

    report_id = fields.Many2one(
        comodel_name="l10n.es.atc.mod415.report",
        string="Modelo 415",
        ondelete="cascade",
        index=1,
        default=_default_record_id,
    )


class L10nEsAtcMod415MoveRecord(models.Model):
    _inherit = "l10n.es.aeat.mod347.move.record"
    _name = "l10n.es.atc.mod415.move.record"
    _description = "Move Record"

    @api.model
    def _default_partner_record(self):
        return self.env.context.get("partner_record_id", False)

    partner_record_id = fields.Many2one(
        comodel_name="l10n.es.atc.mod415.partner_record",
        string="Partner record",
        required=True,
        ondelete="cascade",
        index=True,
        default=_default_partner_record,
    )
