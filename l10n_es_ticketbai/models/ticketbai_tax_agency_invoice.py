# -*- coding: utf-8 -*-
# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _, exceptions


class TicketBAITaxAgencyInvoice(models.Model):
    _name = 'tbai.tax.agency.invoice'
    _description = 'TicketBAI Tax Agency - Invoice Customization'

    tbai_tax_agency_id = fields.Many2one(comodel_name='tbai.tax.agency', required=True)
    name = fields.Char('XML FieldName', required=True)
    min_occurs = fields.Integer('minOccurs', default=1)
    max_occurs = fields.Integer('maxOccurs', default=1)

    _sql_constraints = [
        ('uniq_agency_field', 'UNIQUE(tbai_tax_agency_id,name)',
         _('The field is already been modified for that particular Tax Agency!'))
    ]

    @api.one
    @api.constrains('min_occurs', 'max_occurs')
    def _check_occurs(self):
        if 0 > self.min_occurs:
            raise exceptions.ValidationError(_("minOccurs must be positive!"))
        if 0 > self.max_occurs:
            raise exceptions.ValidationError(_("maxOccurs must be positive!"))
