# -*- coding: utf-8 -*-
# Copyright 2024 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo import exceptions


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_es_verifactu_enabled = fields.Boolean(
        related="company_id.l10n_es_verifactu_enabled", readonly=False
    )
    config_verifactu_developer_name = fields.Char(
        string="Developer Name",
        config_parameter="l10n_es_edi_verifactu.verifactu_developer_name",
    )
    config_verifactu_developer_id = fields.Char(
        string="Developer ID",
        config_parameter="l10n_es_edi_verifactu.verifactu_developer_id",
    )
    config_verifactu_software_id = fields.Char(
        string="Software ID",
        config_parameter="l10n_es_edi_verifactu.verifactu_software_id",
    )
    config_verifactu_software_name = fields.Char(
        string="Name", config_parameter="l10n_es_edi_verifactu.verifactu_software_name"
    )
    config_verifactu_software_number = fields.Char(
        string="Number",
        config_parameter="l10n_es_edi_verifactu.verifactu_software_number",
    )
    config_verifactu_software_version = fields.Char(
        string="Version",
        config_parameter="l10n_es_edi_verifactu.verifactu_software_version",
    )

    @api.constrains("config_verifactu_developer_name")
    def _check_config_verifactu_developer_name(self):
        for setting in self:
            if setting.config_verifactu_developer_name and 120 < len(
                setting.config_verifactu_developer_name
            ):
                raise exceptions.ValidationError(
                    _(
                        "Verifactu: Developer Name %s longer than expected. It must be maximum 120 characters length."
                    )
                    % setting.config_verifactu_developer_name
                )

    @api.constrains("config_verifactu_developer_id")
    def _check_config_verifactu_developer_id(self):
        for setting in self:
            if setting.config_verifactu_developer_id and 9 < len(
                setting.config_verifactu_developer_id
            ):
                raise exceptions.ValidationError(
                    _(
                        "Verifactu: Developer ID %s longer than expected. It must be maximum 9 characters length."
                    )
                    % setting.config_verifactu_developer_id
                )

    @api.constrains("config_verifactu_software_id")
    def _check_config_verifactu_software_id(self):
        for setting in self:
            if setting.config_verifactu_software_id and 2 < len(
                setting.config_verifactu_software_id
            ):
                raise exceptions.ValidationError(
                    _(
                        "Verifactu: Software ID %s longer than expected. It must be maximum 2 characters length."
                    )
                    % setting.config_verifactu_software_id
                )

    @api.constrains("config_verifactu_software_name")
    def _check_config_verifactu_software_name(self):
        for setting in self:
            if setting.config_verifactu_software_name and 30 < len(
                setting.config_verifactu_software_name
            ):
                raise exceptions.ValidationError(
                    _(
                        "Verifactu: Software name %s longer than expected. It must be maximum 30 characters length."
                    )
                    % setting.config_verifactu_software_name
                )

    @api.constrains("config_verifactu_software_number")
    def _check_config_verifactu_software_number(self):
        for setting in self:
            if setting.config_verifactu_software_number and 100 < len(
                setting.config_verifactu_software_number
            ):
                raise exceptions.ValidationError(
                    _(
                        "Verifactu: Software number %s longer than expected. It must be maximum 100 characters length."
                    )
                    % setting.config_verifactu_software_number
                )

    @api.constrains("config_verifactu_software_version")
    def _check_config_verifactu_software_version(self):
        for setting in self:
            if setting.config_verifactu_software_version and 50 < len(
                setting.config_verifactu_software_version
            ):
                raise exceptions.ValidationError(
                    _(
                        "Verifactu: Software version %s longer than expected. It must be maximum 50 characters length."
                    )
                    % setting.config_verifactu_software_version
                )
