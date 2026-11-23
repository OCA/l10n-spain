# Copyright 2014-2023 Binhex - Nicolás Ramos (http://binhex.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models

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

    def _get_key_tax_mapping(self):
        return KEY_TAX_MAPPING

    def _get_not_included_field(self):
        return "not_in_mod415"


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
        default=lambda self: self._default_record_id(),
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

    def get_confirm_url(self):
        self.ensure_one()
        return self._notify_get_action_link("controller", controller="/mod415/accept")

    def get_reject_url(self):
        self.ensure_one()
        return self._notify_get_action_link("controller", controller="/mod415/reject")


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
        default=lambda self: self._default_record_id(),
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
        default=lambda self: self._default_partner_record(),
    )
