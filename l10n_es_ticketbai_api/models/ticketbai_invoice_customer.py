# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from .res_country import CountryCode
from ..utils import utils as tbai_utils
from odoo import models, fields, api, exceptions, _


class TicketBaiCustomerIdType(tbai_utils.EnumValues):
    T02 = '02'
    T03 = '03'
    T04 = '04'
    T05 = '05'
    T06 = '06'


class TicketBaiInvoiceCustomer(models.Model):
    _name = 'tbai.invoice.customer'
    _description = 'TicketBAI Invoice recipients'

    tbai_invoice_id = fields.Many2one(
        comodel_name='tbai.invoice', required=True, ondelete='cascade')
    name = fields.Char(help='Name and surname, or business name.', required=True)
    country_code = fields.Char(required=True)
    nif = fields.Char('NIF', default='', help='Spanish Fiscal Identification Number')
    identification_number = fields.Char(
        default='', help='Required Identification Number for non spanish customers.')
    idtype = fields.Selection(selection=[
        (TicketBaiCustomerIdType.T02.value, 'VAT identification number'),
        (TicketBaiCustomerIdType.T03.value, 'Passport'),
        (TicketBaiCustomerIdType.T04.value,
         'Official identification document issued by the country or territory of '
         'residence'),
        (TicketBaiCustomerIdType.T05.value, 'Residence certificate'),
        (TicketBaiCustomerIdType.T06.value, 'Other document')
    ], string='Identification Type Code', default=TicketBaiCustomerIdType.T02.value,
        help='Required for non spanish customers.')
    address = fields.Char(default='')
    zip = fields.Char('ZIP Code', default='')

    @api.multi
    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if 120 < len(record.name):
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "Customer name %s longer than expected. "
                    "Should be 120 characters max.!"
                ) % (record.tbai_invoice_id.name, record.name))

    @api.multi
    @api.constrains('country_code')
    def _check_country_code(self):
        for record in self:
            if record.country_code not in CountryCode.values():
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s: Customer %s Country Code %s not valid."
                ) % (record.tbai_invoice_id.name, record.name, record.country_code))

    @api.multi
    @api.constrains('nif')
    def _check_nif(self):
        for record in self:
            if record.nif:
                tbai_utils.check_spanish_vat_number(_(
                    "TicketBAI Invoice %s: Customer %s NIF"
                ) % (record.tbai_invoice_id.name, record.name), record.nif)
            elif not record.idtype and not record.identification_number:
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "Spanish Fiscal Identification Number or "
                    "Identification Number for non spanish customers is required."
                ) % record.tbai_invoice_id.name)

    @api.multi
    @api.constrains('identification_number')
    def _check_identification_number(self):
        for record in self:
            if record.identification_number and 20 < len(record.identification_number):
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "Customer %s Identification Number %s longer than expected. "
                    "Should be 20 characters max.!"
                ) % (record.tbai_invoice_id.name, record.name,
                     record.identification_number))
            elif not record.nif and record.idtype and not record.identification_number:
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "Customer %s Identification Number for non spanish customers is "
                    "required.") % (record.tbai_invoice_id.name, record.name))

    @api.multi
    @api.constrains('idtype')
    def _check_idtype(self):
        for record in self:
            if not record.idtype and not record.nif:
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "Customer %s Spanish Fiscal Identification Number or "
                    "Identification Number for non spanish customers is required."
                ) % (record.tbai_invoice_id.name, record.name))

    @api.multi
    @api.constrains('address')
    def _check_address(self):
        for record in self:
            if record.address and 250 < len(record.address):
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "Customer %s Address %s longer than expected. "
                    "Should be 250 characters max.!"
                ) % (record.tbai_invoice_id.name, record.name, record.address))

    @api.multi
    @api.constrains('zip')
    def _check_zip(self):
        for record in self:
            if record.zip and 20 < len(record.zip):
                raise exceptions.ValidationError(_(
                    "TicketBAI Invoice %s:\n"
                    "Customer %s ZIP Code %s longer than expected. "
                    "Should be 20 characters max.!"
                ) % (record.tbai_invoice_id.name, record.name, record.zip))
