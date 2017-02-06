# -*- coding: utf-8 -*-
# (c) 2017 Alfredo de la Fuente - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openerp import models, fields


class L10nEsAeatMod347PartnerRecord(models.Model):
    _inherit = 'l10n.es.aeat.mod347.partner_record'

    company_id = fields.Many2one(
        related='report_id.company_id', store=True)
    report_identifier = fields.Char(
        related='report_id.name', store=True)
    company_vat = fields.Char(
        related='report_id.company_vat', store=True)
    fiscalyear_id = fields.Many2one(
        related='report_id.fiscalyear_id', store=True)
    period_type = fields.Selection(
        related='report_id.period_type', store=True)
