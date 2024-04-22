# -*- coding: utf-8 -*-
# Copyright 2024 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class Company(models.Model):
    _inherit = "res.company"

    l10n_es_verifactu_enabled = fields.Boolean(string="Enable Verifactu", default=False)
    l10n_es_verifactu_chain_sequence_id = fields.Many2one(
        comodel_name="ir.sequence",
        string="Verifactu account.move chain sequence",
        readonly=True,
        copy=False,
    )

    def get_l10n_es_verifactu_license_dict(self):
        # sudo() why: ir.config_parameter is only accessible for base.group_system
        SudoParam = self.env["ir.config_parameter"].sudo()
        return {
            "developer_name": SudoParam.get_param(
                "l10n_es_edi_verifactu.verifactu_developer_name", ""
            ),
            "developer_id": SudoParam.get_param(
                "l10n_es_edi_verifactu.verifactu_developer_id", ""
            ),
            "software_id": SudoParam.get_param(
                "l10n_es_edi_verifactu.verifactu_software_id", ""
            ),
            "software_name": SudoParam.get_param(
                "l10n_es_edi_verifactu.verifactu_software_name", ""
            ),
            "software_number": SudoParam.get_param(
                "l10n_es_edi_verifactu.verifactu_software_number", ""
            ),
            "software_version": SudoParam.get_param(
                "l10n_es_edi_verifactu.verifactu_software_version", ""
            ),
        }

    def get_l10n_es_verifactu_next_chain_index(self):
        self.ensure_one()
        if not self.l10n_es_verifactu_chain_sequence_id:
            # sudo() why: company write grants only for group_system
            # sudo() why: ir.sequence create grants only for group_system
            sudo_self = self.sudo()
            sudo_self.l10n_es_verifactu_chain_sequence_id = sudo_self.env[
                "ir.sequence"
            ].create(
                {
                    "name": f"Verifactu account move sequence for {self.name} (id: {self.id})",
                    "code": f"l10n_es.edi.verifactu.account.move.{self.id}",
                    "implementation": "no_gap",
                    "company_id": self.id,
                }
            )
        return self.l10n_es_verifactu_chain_sequence_id.next_by_id()

    def get_l10n_es_verifactu_last_posted_invoice(self):
        domain = [
            ("l10n_es_edi_verifactu_chain_index", "!=", 0),
            ("company_id", "=", self.id),
        ]
        return self.env["account.move"].search(
            domain, limit=1, order="l10n_es_edi_verifactu_chain_index desc"
        )
