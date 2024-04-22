# -*- coding: utf-8 -*-
# Copyright 2024 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountEdiDocument(models.Model):
    _inherit = "account.edi.document"

    def _prepare_jobs(self):
        # TODO filter jobs to send according to ControlFlujoEnvios parameters
        jobs = super()._prepare_jobs()
        return jobs
