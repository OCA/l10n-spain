# -*- coding: utf-8 -*-
# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models, fields, exceptions, _


class TicketBAITaxAgency(models.Model):
    _name = 'tbai.tax.agency'
    _description = 'TicketBAI Tax Agency'

    name = fields.Char(string='Tax Agency', required=True)
    version = fields.Char(string='TicketBAI version',
                          compute='_compute_ticketbai_version', store=True)
    qr_base_url = fields.Char(string='QR Base URL',
                              compute='_compute_ticketbai_version', store=True)
    tax_agency_version_ids = fields.One2many(comodel_name='tbai.tax.agency.version',
                                             inverse_name='tbai_tax_agency_id')

    def _get_tbai_tax_agency_version(self):
        self.ensure_one()

    @api.multi
    @api.depends(
        'tax_agency_version_ids',
        'tax_agency_version_ids.date_from', 'tax_agency_version_ids.date_to',
        'tax_agency_version_ids.version'
    )
    def _compute_ticketbai_version(self):
        for record in self:
            today = fields.Date.today()
            search_domain = [
                ('tbai_tax_agency_id', '=', record.id),
                '|', ('date_from', '<=', today), ('date_from', '=', False),
                '|', ('date_to', '>=', today), ('date_to', '=', False)
            ]
            tax_agency_version = self.env['tbai.tax.agency.version'].search(
                search_domain)
            record.version = tax_agency_version.version
            record.qr_base_url = tax_agency_version.qr_base_url

    def tbai_get_value_id_version_tbai(self):
        """ V 1.1
        <element name="IDVersionTBAI" type="T:TextMax5Type"/>
            <maxLength value="5"/>
        :return: TicketBAI current version
        """
        return self.version


class TicketBAITaxAgencyVersion(models.Model):
    _name = 'tbai.tax.agency.version'
    _description = 'TicketBAI Tax Agency - version'

    @api.one
    @api.constrains("version")
    def _check_ticketbai_version(self):
        if len(self.version) not in range(1, 6):
            raise exceptions.ValidationError(
                _("TicketBAI version max size is 5 characters."))

    @api.one
    @api.constrains('date_from', 'date_to')
    def _unique_date_range(self):
        # Based in l10n_es_aeat module
        domain = [('id', '!=', self.id),
                  ('tbai_tax_agency_id', '=', self.tbai_tax_agency_id.id)]
        if self.date_from and self.date_to:
            domain += ['|', '&',
                       ('date_from', '<=', self.date_to),
                       ('date_from', '>=', self.date_from),
                       '|', '&',
                       ('date_to', '<=', self.date_to),
                       ('date_to', '>=', self.date_from),
                       '|', '&',
                       ('date_from', '=', False),
                       ('date_to', '>=', self.date_from),
                       '|', '&',
                       ('date_to', '=', False),
                       ('date_from', '<=', self.date_to),
                       ]
        elif self.date_from:
            domain += [('date_to', '>=', self.date_from)]
        elif self.date_to:
            domain += [('date_from', '<=', self.date_to)]
        date_lst = self.search(domain)
        if date_lst:
            raise exceptions.ValidationError(
                _("Error! The dates of the record overlap with an existing record."))

    tbai_tax_agency_id = fields.Many2one(comodel_name='tbai.tax.agency', required=True,
                                         ondelete='restrict')
    version = fields.Char(string='TicketBAI version', required=True)
    date_from = fields.Date(string='Date from')
    date_to = fields.Date(string='Date to')
    qr_base_url = fields.Char(string='QR Base URL', required=True)
