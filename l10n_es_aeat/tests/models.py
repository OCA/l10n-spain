# Copyright 2021 Sygel - Valentin Vinagre
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class L10nEsAeatTestReport(models.Model):
    _name = "l10n.es.aeat.mod999.report"
    _inherit = "l10n.es.aeat.report"
    _description = "L10nEsAeatTestReport"
    _aeat_number = "999"
