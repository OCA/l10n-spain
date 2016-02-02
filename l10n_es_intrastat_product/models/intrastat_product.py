# -*- encoding: utf-8 -*-
##############################################################################
#
#    l10n Spain Report intrastat product module for Odoo
#    Copyright (C) 2010-2015 Akretion (http://www.akretion.com)
#    Copyright (C) 2015 FactorLibre (http://www.factorlibre.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#    @author Ismael Calvo <ismael.calvo@factorlibre.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, _
from openerp.exceptions import Warning, ValidationError
import openerp.addons.decimal_precision as dp
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging

logger = logging.getLogger(__name__)


class L10nEsReportIntrastatProduct(models.Model):
    _name = "l10n.es.report.intrastat.product"
    _description = "Intrastat Product for Spain"
    _rec_name = "start_date"
    _inherit = ['mail.thread', 'intrastat.common']
    _order = "start_date desc, type"
    _track = {
        'state': {
            'l10n_es_intrastat_product.l10n_es_declaration_done':
            lambda self, cr, uid, obj, ctx=None: obj.state == 'done',
        }
    }

    @api.one
    @api.depends(
        'intrastat_line_ids', 'intrastat_line_ids.amount_company_currency',
        'intrastat_line_ids.intrastat_type_id')
    def _compute_total_fiscal_amount(self):
        total_fiscal_amount = 0.0
        for line in self.intrastat_line_ids:
            total_fiscal_amount +=\
                line.amount_company_currency *\
                line.intrastat_type_id.fiscal_value_multiplier
        self.total_fiscal_amount = total_fiscal_amount

    # @api.model
    # def _default_type(self):
    #     if self.company_id.import_obligation_level == 'none':
    #         return 'export'
    #     else:
    #         return False

    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        states={'done': [('readonly', True)]},
        default=lambda self: self.env['res.company']._company_default_get(
            'l10n.es.report.intrastat.product'))
    start_date = fields.Date(
        string='Start Date', required=True,
        states={'done': [('readonly', True)]}, copy=False,
        default=lambda self:
        datetime.today() + relativedelta(day=1, months=-1),
        help="Start date of the declaration. Must be the first day of "
        "a month.")
    end_date = fields.Date(
        compute='_compute_dates', string='End Date', readonly=True, store=True,
        help="End date for the declaration. Is the last day of the "
        "month of the start date.")
    year_month = fields.Char(
        compute='_compute_dates', string='Month', readonly=True,
        track_visibility='always', store=True,
        help="Year and month of the declaration.")
    type = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export')
    ], 'Type', required=True, states={'done': [('readonly', True)]},
        track_visibility='always', help="Select the type of DEB.")
    # ¿Es necesario tener en cuenta el 'oblication_level' para España?
    # obligation_level = fields.Selection([
    #     ('detailed', 'Detailed'),
    #     ('simplified', 'Simplified')
    # ], string='Obligation Level', required=True, track_visibility='always',
    #     states={'done': [('readonly', True)]},
    #     help="Your obligation level for a certain type of DEB "
    #     "(Import or Export) depends on the total value that you export "
    #     "or import per year. Note that the obligation level 'Simplified' "
    #     "doesn't exist for an Import DEB.")
    intrastat_line_ids = fields.One2many(
        'l10n.es.report.intrastat.product.line',
        'parent_id', string='Report Intrastat Product Lines',
        states={'done': [('readonly', True)]})
    num_lines = fields.Integer(
        compute='_compute_numbers', string='Number of Lines', store=True,
        track_visibility='always', help="Number of lines in this declaration.")
    total_amount = fields.Float(
        compute='_compute_numbers', digits=dp.get_precision('Account'),
        string='Total Amount', store=True,
        help="Total amount in company currency of the declaration.")
    total_fiscal_amount = fields.Float(
        compute='_compute_total_fiscal_amount',
        digits=dp.get_precision('Account'),
        string='Total Fiscal Amount', track_visibility='always', store=True,
        help="Total fiscal amount in company currency of the declaration. "
        "This is the total amount that is displayed on the Prodouane website.")
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', readonly=True,
        string='Currency')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], string='State', readonly=True, track_visibility='onchange',
        copy=False, default='draft',
        help="State of the declaration. When the state is set to 'Done', "
        "the parameters become read-only.")
    # No more need for date_done, because chatter does the job

    @api.multi
    def type_on_change(
            self, company_id=False, type=False, context=None):
        pass

        # ¿Es necesario tener en cuenta el 'oblication_level' para España?

        # result = {}
        # result['value'] = {}
        # if type and company_id:
        #     company = self.env['res.company'].browse(company_id)
        #     if type == 'import':
        #         if company.import_obligation_level:
        #             if company.import_obligation_level == 'detailed':
        #                 result['value']['obligation_level'] =\
        #                     company.import_obligation_level
        #             elif company.import_obligation_level == 'none':
        #                 result['warning'] = {
        #                     'title': _("Warning on the Obligation Level"),
        #                     'message':
        #                     _("You are tying to make an "
        #                         "Intrastat Product of type 'Import', "
        #                         "but the Import Obligation Level set "
        #                         "for your company is 'None'. If this "
        #                         "parameter on your company is correct, "
        #                         "you should NOT create an Import Intrastat "
        #                         "Product."),
        #                 }
        #     if type == 'export':
        #         if company.export_obligation_level:
        #             result['value']['obligation_level'] =\
        #                 company.export_obligation_level
        # return result

    @api.constrains('start_date')
    def _product_check_start_date(self):
        self._check_start_date()

    # @api.one
    # @api.constrains('type', 'obligation_level')
    # def _check_obligation_level(self):
    #     if self.type == 'import' and self.obligation_level == 'simplified':
    #         raise ValidationError(
    #             _("Obligation level can't be 'Simplified' for Import"))

    _sql_constraints = [(
        'date_company_type_uniq',
        'unique(start_date, company_id, type)',
        'A DEB of the same type already exists for this month !')]

    @api.multi
    def create_intrastat_product_lines(self, invoice, parent_values):
        """This function is called for each invoice"""
        self.ensure_one()
        line_obj = self.env['l10n.es.report.intrastat.product.line']
        weight_uom_categ = self.env.ref('product.product_uom_categ_kgm')
        kg_uom = self.env.ref('product.product_uom_kgm')
        pce_uom_categ = self.env.ref('product.product_uom_categ_unit')
        pce_uom = self.env.ref('product.product_uom_unit')

        lines_to_create = []
        total_invoice_cur_accessory_cost = 0.0
        total_invoice_cur_product_value = 0.0
        for line in invoice.invoice_line:
            line_qty = line.quantity
            source_uom = line.uos_id

            # We don't do anything when there is no product_id...
            # this may be a problem... but i think a raise would be too violent
            if not line.product_id:
                continue

            if line.product_id.exclude_from_intrastat:
                continue

            if not line_qty:
                continue

            # If type = "service" and is_accessory_cost=True, then we keep
            # the line (it will be skipped later on)
            if (
                    line.product_id.type not in ('product', 'consu')
                    and not line.product_id.is_accessory_cost):
                continue

            skip_this_line = False
            for line_tax in line.invoice_line_tax_id:
                if line_tax.exclude_from_intrastat_if_present:
                    skip_this_line = True
            if skip_this_line:
                continue
            if (
                    line.product_id.is_accessory_cost
                    and line.product_id.type == 'service'):
                total_invoice_cur_accessory_cost += line.price_subtotal
                continue
            # END OF "continue" instructions
            # AFTER THIS POINT, we are sure to have real products that
            # have to be declared to DEB
            amount_product_value_inv_cur_to_write = line.price_subtotal
            total_invoice_cur_product_value += line.price_subtotal
            invoice_currency_id_to_write = invoice.currency_id.id

            if not parent_values['is_fiscal_only']:

                if not source_uom:
                    raise Warning(
                        _("Missing unit of measure on the line with %d "
                            "product(s) '%s' on invoice '%s'.")
                        % (line_qty, line.product_id.name, invoice.number))
                else:
                    source_uom_id_to_write = source_uom.id

                if source_uom == kg_uom:
                    weight_to_write = line_qty
                elif source_uom.category_id == weight_uom_categ:
                    weight_to_write = self.env['product.uom']._compute_qty_obj(
                        source_uom, line_qty, kg_uom)
                elif source_uom.category_id == pce_uom_categ:
                    if not line.product_id.weight_net:
                        raise Warning(
                            _("Missing net weight on product '%s'.")
                            % (line.product_id.name))
                    if source_uom == pce_uom:
                        weight_to_write = line.product_id.weight_net * line_qty
                    else:
                        # Here, I suppose that, on the product, the
                        # weight is per PCE and not per uom_id
                        weight_to_write = line.product_id.weight_net * \
                            self.env['product.uom']._compute_qty_obj(
                                source_uom, line_qty, pce_uom)

                else:
                    raise Warning(
                        _("Conversion from unit of measure '%s' to 'Kg' "
                            "is not implemented yet.")
                        % (source_uom.name))

                product_intrastat_code = line.product_id.hs_code_id
                if not product_intrastat_code:
                    # If the H.S. code is not set on the product,
                    # we check if it's set on it's related category
                    product_intrastat_code =\
                        line.product_id.categ_id.hs_code_id
                    if not product_intrastat_code:
                        raise Warning(
                            _("Missing H.S. code on product '%s' or on it's "
                                "related category '%s'.") % (
                                line.product_id.name,
                                line.product_id.categ_id.complete_name))
                intrastat_code_id_to_write = product_intrastat_code.id

                if not product_intrastat_code.hs_code:
                    raise Warning(
                        _("Missing intrastat code on H.S. code '%s' (%s).") % (
                            product_intrastat_code.name,
                            product_intrastat_code.description))
                else:
                    intrastat_code_to_write =\
                        product_intrastat_code.hs_code

                if not product_intrastat_code.intrastat_unit_id:
                    intrastat_uom_id_to_write = False
                    quantity_to_write = False
                else:
                    intrastat_uom_id_to_write =\
                        product_intrastat_code.intrastat_unit_id.uom_id.id
                    if intrastat_uom_id_to_write == source_uom_id_to_write:
                        quantity_to_write = line_qty
                    elif (
                            source_uom.category_id ==
                            product_intrastat_code.intrastat_unit_id.uom_id.
                            category_id):
                        quantity_to_write =\
                            source_uom._compute_qty_obj(
                                source_uom, line_qty,
                                product_intrastat_code.intrastat_unit_id.uom_id
                            )
                    else:
                        raise Warning(
                            _("On invoice '%s', the line with product '%s' "
                                "has a unit of measure (%s) which can't be "
                                "converted to UoM of it's intrastat "
                                "code (%s).") % (
                                invoice.number,
                                line.product_id.name,
                                source_uom_id_to_write,
                                intrastat_uom_id_to_write))

                # The origin country should only be declated on Import
                if self.type == 'export':
                    product_origin_country_id_to_write = False
                elif line.product_id.origin_country_id:
                    # If we have the country of origin on the product: take it
                    product_origin_country_id_to_write =\
                        line.product_id.origin_country_id.id
                else:
                    # If we don't, look on the product supplier info
                    origin_partner_id =\
                        parent_values.get('origin_partner_id', False)
                    if origin_partner_id:
                        supplieri_obj = self.env['product.supplierinfo']
                        suppliers = supplieri_obj.search([
                            ('name', '=', origin_partner_id),
                            (
                                'product_tmpl_id',
                                '=',
                                line.product_id.product_tmpl_id.id),
                            ('origin_country_id', '!=', False)
                        ])
                        if not suppliers:
                            raise Warning(
                                _("Missing country of origin on product '%s' "
                                    "or on it's supplier information for "
                                    "partner '%s'.") % (
                                    line.product_id.name,
                                    parent_values.get(
                                        'origin_partner_name', 'none')))
                        else:
                            product_origin_country_id_to_write =\
                                suppliers[0].origin_country_id.id
                    else:
                        raise Warning(
                            _("Missing country of origin on product '%s' "
                                "(it's not possible to get the country of "
                                "origin from the 'supplier information' in "
                                "this case because we don't know the "
                                "supplier of this product for the "
                                "invoice '%s').")
                            % (line.product_id.name, invoice.number))

            else:
                weight_to_write = False
                source_uom_id_to_write = False
                intrastat_code_id_to_write = False
                intrastat_code_to_write = False
                quantity_to_write = False
                intrastat_uom_id_to_write = False
                product_origin_country_id_to_write = False

            if not parent_values.get('incoterm_id', False):
                raise Warning(
                    _("Missing incoterm on invoice '%s'. You can set a "
                        "default one on the company")
                    % (invoice.number))

            create_new_line = True
            for line_to_create in lines_to_create:
                if (
                        line_to_create.get('intrastat_code_id', False) ==
                        intrastat_code_id_to_write
                        and line_to_create.get('source_uom_id', False) ==
                        source_uom_id_to_write
                        and line_to_create.get('intrastat_type_id', False) ==
                        parent_values['intrastat_type_id_to_write']
                        and line_to_create.get(
                            'product_origin_country_id', False) ==
                        product_origin_country_id_to_write):
                    create_new_line = False
                    line_to_create['quantity'] += quantity_to_write
                    line_to_create['weight'] += weight_to_write
                    line_to_create['amount_product_value_inv_cur'] +=\
                        amount_product_value_inv_cur_to_write
                    break
            if create_new_line:
                lines_to_create.append({
                    'parent_id': self.id,
                    'invoice_id': invoice.id,
                    'quantity': quantity_to_write,
                    'source_uom_id': source_uom_id_to_write,
                    'intrastat_uom_id': intrastat_uom_id_to_write,
                    'partner_country_id':
                    parent_values['partner_country_id_to_write'],
                    'intrastat_code': intrastat_code_to_write,
                    'intrastat_code_id': intrastat_code_id_to_write,
                    'weight': weight_to_write,
                    'product_origin_country_id':
                    product_origin_country_id_to_write,
                    'transport': parent_values['transport_to_write'],
                    'state': parent_values['state_to_write'],
                    'intrastat_type_id':
                    parent_values['intrastat_type_id_to_write'],
                    'procedure_code': parent_values['procedure_code_to_write'],
                    'transaction_code':
                    parent_values['transaction_code_to_write'],
                    'partner_id': parent_values['partner_id_to_write'],
                    'invoice_currency_id': invoice_currency_id_to_write,
                    'amount_product_value_inv_cur':
                    amount_product_value_inv_cur_to_write,
                    'is_fiscal_only': parent_values['is_fiscal_only'],
                    'incoterm_id': parent_values['incoterm_id'],
                })
        # End of the loop on invoice lines

        # Why do I manage the Partner VAT number only here and not earlier
        # in the code ?
        # Because, if I sell to a physical person in the EU with VAT, then
        # the corresponding partner will not have a VAT number, and the entry
        # will be skipped because line_tax.exclude_from_intrastat_if_present
        # is always True
        # So we should not block with a raise before the end of the loop on the
        # invoice lines
        if lines_to_create:
            if parent_values['is_vat_required']:
                # If I have invoice.intrastat_country_id and the invoice
                # partner is outside the EU, then I look for the fiscal rep
                # of the partner
                if (
                        invoice.intrastat_country_id
                        and not invoice.partner_id.country_id.intrastat):
                    if not invoice.partner_id.intrastat_fiscal_representative:
                        raise Warning(
                            _("Missing fiscal representative for partner "
                                "'%s'. It is required for invoice '%s' which "
                                "has an invoice partner outside the EU but "
                                "the goods were delivered to or received "
                                "from inside the EU.")
                            % (invoice.partner_id.name, invoice.number))
                    else:
                        parent_values['partner_vat_to_write'] =\
                            invoice.partner_id.\
                            intrastat_fiscal_representative.vat
                # Otherwise, I just read the vat number on the partner
                # of the invoice
                else:

                    if not invoice.partner_id.vat:
                        raise Warning(
                            _("Missing VAT number on partner '%s'.")
                            % invoice.partner_id.name)
                    else:
                        parent_values['partner_vat_to_write'] =\
                            invoice.partner_id.vat
            else:
                parent_values['partner_vat_to_write'] = False

        for line_to_create in lines_to_create:
            line_to_create['partner_vat'] =\
                parent_values['partner_vat_to_write']

            if not total_invoice_cur_accessory_cost:
                line_to_create['amount_accessory_cost_inv_cur'] = 0
            else:
                if total_invoice_cur_product_value:
                    # The accessory costs are added at the pro-rata of value
                    line_to_create['amount_accessory_cost_inv_cur'] =\
                        total_invoice_cur_accessory_cost *\
                        line_to_create['amount_product_value_inv_cur']\
                        / total_invoice_cur_product_value
                else:
                    # The accessory costs are added at the pro-rata
                    # of the number of lines
                    line_to_create['amount_accessory_cost_inv_cur'] =\
                        total_invoice_cur_accessory_cost / len(lines_to_create)

            line_to_create['amount_invoice_currency'] =\
                line_to_create['amount_product_value_inv_cur'] +\
                line_to_create['amount_accessory_cost_inv_cur']

            # We do currency conversion NOW
            if invoice.currency_id.name != 'EUR':
                # for currency conversion
                line_to_create['amount_company_currency'] =\
                    self.env['res.currency'].with_context(
                        date=invoice.date_invoice).compute(
                        invoice.currency_id,
                        self.company_id.currency_id,
                        line_to_create['amount_invoice_currency'])
            else:
                line_to_create['amount_company_currency'] =\
                    line_to_create['amount_invoice_currency']
            # We round
            line_to_create['amount_company_currency'] = int(
                round(line_to_create['amount_company_currency']))
            if line_to_create['amount_company_currency'] == 0:
                # p20 of the BOD :
                # lines with value rounded to 0 mustn't be declared
                continue
            for value in ['quantity', 'weight']:  # These 2 fields are char
                if line_to_create[value]:
                    line_to_create[value] = str(
                        int(round(line_to_create[value], 0)))
            line_obj.create(line_to_create)
        return True

    @api.multi
    def compute_invoice_values(self, invoice, parent_values):
        self.ensure_one()
        intrastat_type = self.env['report.intrastat.type'].browse(
            parent_values['intrastat_type_id_to_write'])
        parent_values['procedure_code_to_write'] =\
            intrastat_type.procedure_code
        parent_values['transaction_code_to_write'] =\
            intrastat_type.transaction_code
        parent_values['is_fiscal_only'] = intrastat_type.is_fiscal_only
        parent_values['is_vat_required'] = intrastat_type.is_vat_required

        # if self.obligation_level == 'simplified':
        #     # force to is_fiscal_only
        #     parent_values['is_fiscal_only'] = True

        if not parent_values['is_fiscal_only']:
            if not invoice.intrastat_transport:
                if not self.company_id.default_intrastat_transport:
                    raise Warning(
                        _("The mode of transport is not set on invoice "
                            "'%s' nor the default mode of transport on "
                            "the company '%s'.")
                        % (invoice.number, self.company_id.name))
                else:
                    parent_values['transport_to_write'] =\
                        self.company_id.default_intrastat_transport
            else:
                parent_values['transport_to_write'] =\
                    invoice.intrastat_transport

            if not invoice.intrastat_state:
                if not self.company_id.default_intrastat_state:
                    raise Warning(
                        _("The intrastat state hasn't been set on "
                            "invoice '%s' and the default intrastat "
                            "state is missing on the company '%s'.")
                        % (invoice.number, self.company_id.name))
                else:
                    parent_values['state_to_write'] =\
                        self.company_id.default_intrastat_state.id
            else:
                parent_values['state_to_write'] =\
                    invoice.intrastat_state.id
        else:
            parent_values['state_to_write'] = False
            parent_values['transport_to_write'] = False
            parent_values['transaction_code_to_write'] = False
            parent_values['partner_country_id_to_write'] = False
        return parent_values

    @api.multi
    def generate_product_lines_from_invoice(self):
        '''Function called by the button on form view'''
        self.ensure_one()
        self._check_generate_lines()
        line_obj = self.env['l10n.es.report.intrastat.product.line']
        to_remove_lines = line_obj.search([
            ('parent_id', '=', self.id),
            ('invoice_id', '!=', False)])
        if to_remove_lines:
            to_remove_lines.unlink()

        invoice_obj = self.env['account.invoice']
        invoice_type = False
        if self.type == 'import':
            # Les régularisations commerciales à l'HA ne sont PAS déclarées
            # dans la DEB, cf page 50 du BOD 6883 du 06 janvier 2011
            invoice_type = ('in_invoice', )
        elif self.type == 'export':
            invoice_type = ('out_invoice', 'out_refund')
        invoices = invoice_obj.search([
            ('type', 'in', invoice_type),
            ('date_invoice', '<=', self.end_date),
            ('date_invoice', '>=', self.start_date),
            ('state', 'in', ('open', 'paid')),
            ('company_id', '=', self.company_id.id)
        ], order='date_invoice')
        for invoice in invoices:
            parent_values = {}

            # We should always have a country on partner_id
            if not invoice.partner_id.country_id:
                raise Warning(
                    _("Missing country on partner '%s'.")
                    % invoice.partner_id.name)

            # If I have no invoice.intrastat_country_id, which is the
            # case the first month of the deployment of the module,
            # then I use the country on invoice partner
            if not invoice.intrastat_country_id:
                if not invoice.partner_id.country_id.intrastat:
                    continue
                elif (
                        invoice.partner_id.country_id ==
                        self.company_id.country_id):
                    continue
                else:
                    parent_values['partner_country_id_to_write'] =\
                        invoice.partner_id.country_id.id

            # If I have invoice.intrastat_country_id, which should be
            # the case after the first month of use of the module, then
            # I use invoice.intrastat_country_id
            else:
                if not invoice.intrastat_country_id.intrastat:
                    continue
                elif (
                        invoice.intrastat_country_id ==
                        self.company_id.country_id):
                    continue
                else:
                    parent_values['partner_country_id_to_write'] =\
                        invoice.intrastat_country_id.id
            if not invoice.intrastat_type_id:
                if invoice.type == 'out_invoice':
                    if self.company_id.default_intrastat_type_out_invoice:
                        parent_values['intrastat_type_id_to_write'] =\
                            self.company_id.\
                            default_intrastat_type_out_invoice.id
                    else:
                        raise Warning(
                            _("The intrastat type hasn't been set on "
                                "invoice '%s' and the 'default intrastat "
                                "type for customer invoice' is missing "
                                "for the company '%s'.")
                            % (invoice.number, self.company_id.name))
                elif invoice.type == 'out_refund':
                    if self.company_id.default_intrastat_type_out_refund:
                        parent_values['intrastat_type_id_to_write'] =\
                            self.company_id.\
                            default_intrastat_type_out_refund.id
                    else:
                        raise Warning(
                            _("The intrastat type hasn't been set on refund "
                                "'%s' and the 'default intrastat type for "
                                "customer refund' is missing for the "
                                "company '%s'.")
                            % (invoice.number, self.company_id.name))
                elif invoice.type == 'in_invoice':
                    if self.company_id.default_intrastat_type_in_invoice:
                        parent_values['intrastat_type_id_to_write'] =\
                            self.company_id.\
                            default_intrastat_type_in_invoice.id
                    else:
                        raise Warning(
                            _("The intrastat type hasn't been set on "
                                "invoice '%s' and the 'Default intrastat "
                                "type for supplier invoice' is missing "
                                "for the company '%s'.")
                            % (invoice.number, self.company_id.name))
                elif invoice.type == 'in_refund':
                    if self.company_id.default_intrastat_type_in_refund:
                        parent_values['intrastat_type_id_to_write'] =\
                            self.company_id.\
                            default_intrastat_type_in_refund.id
                    else:
                        raise Warning(
                            _("The intrastat type hasn't been set on "
                                "invoice '%s' and the 'Default intrastat "
                                "type for supplier refund' is missing "
                                "for the company '%s'.")
                            % (invoice.number, self.company_id.name))

            else:
                parent_values['intrastat_type_id_to_write'] =\
                    invoice.intrastat_type_id.id

            if (
                    invoice.intrastat_country_id
                    and not invoice.partner_id.country_id.intrastat
                    and invoice.partner_id.intrastat_fiscal_representative):
                # fiscal rep
                parent_values['partner_id_to_write'] =\
                    invoice.partner_id.intrastat_fiscal_representative.id
            else:
                parent_values['partner_id_to_write'] = invoice.partner_id.id
            if not invoice.incoterm_id:
                if self.company_id.default_incoterm:
                    parent_values['incoterm_id'] =\
                        self.company_id.default_incoterm.id
            else:
                parent_values['incoterm_id'] = self.incoterm_id.id

            # Get partner on which we will check the 'country of origin'
            # on product_supplierinfo
            parent_values['origin_partner_id'] = invoice.partner_id.id
            parent_values['origin_partner_name'] = invoice.partner_id.name

            parent_values = self.compute_invoice_values(invoice, parent_values)

            self.create_intrastat_product_lines(invoice, parent_values)
        return True

    @api.multi
    def done(self):
        self.write({'state': 'done'})
        return True

    @api.multi
    def back2draft(self):
        self.write({'state': 'draft'})
        return True

    @api.multi
    def generate_csv(self):
        '''Generate the AEAT csv file export.'''
        if not self.intrastat_line_ids:
            raise ValidationError(_('There is not any product line'))
        rows = []
        for line in self.intrastat_line_ids:
            # TO DO port/airport
            rows.append((
                line.partner_country_code,  # Estado destino/origen
                line.state.code,  # Provincia destino/origen # state_code
                line.incoterm_code,  # Condiciones de entrega
                line.transaction_code,  # Naturaleza de la transacción
                line.transport,  # Modalidad de transporte
                False,  # Puerto/Aeropuerto de carga o descarga
                line.intrastat_code,  # Código mercancías CN8
                line.product_country_origin_code,  # País origen
                line.procedure_code,  # Régimen estadístico
                line.weight,  # Peso
                line.quantity,  # Unidades suplementarias
                line.amount_company_currency,  # Importe facturado
                False,  # Valor estadístico
            ))

        csv_string = self._format_csv(rows, ';')
        attach_id = self._attach_csv_file(csv_string, 'aeat')
        return self._open_attach_view(attach_id, title="AEAT csv file")

    # TO DO in intrastat_base.intrastat_common
    @api.multi
    def _format_csv(self, rows, delimiter):
        csv_string = ''
        for row in rows:
            for field in row:
                csv_string += field and str(field) or ''
                csv_string += delimiter
            csv_string += '\n'
        return csv_string

    # TO DO in intrastat_base.intrastat_common
    @api.multi
    def _attach_csv_file(self, csv_string, declaration_name):
        '''Attach the XML file to the report_intrastat_product/service
        object'''
        self.ensure_one()
        import base64
        filename = '%s_%s.csv' % (self.year_month, declaration_name)
        attach = self.env['ir.attachment'].create({
            'name': filename,
            'res_id': self.id,
            'res_model': self._name,
            'datas': base64.encodestring(csv_string),
            'datas_fname': filename})
        return attach.id

    @api.model
    def _scheduler_reminder(self):
        previous_month = datetime.strftime(
            datetime.today() + relativedelta(day=1, months=-1), '%Y-%m')
        # I can't search on [('country_id', '=', ..)]
        # because it is a fields.function not stored and without fnct_search
        companies = self.env['res.company'].search([])
        logger.info('Starting the Intrastat Product reminder')
        for company in companies:
            if company.country_id.code != 'ES':
                continue
            for type in ['import', 'export']:
                # if (
                #         type == 'import'
                #         and company.import_obligation_level == 'none'):
                #     continue
                # Check if a declaration already exists for month N-1
                intrastats = self.search([
                    ('year_month', '=', previous_month),
                    ('type', '=', type),
                    ('company_id', '=', company.id)
                ])
                if intrastats:
                    # if it already exists, we don't do anything
                    logger.info(
                        'An %s Intrastat Product for month %s already '
                        'exists for company %s'
                        % (type, previous_month, company.name))
                    continue
                else:
                    # If not, we create one for month N-1
                    # obligation_level = eval(
                    #     'company.%s_obligation_level' % type)
                    # if not obligation_level:
                    #     logger.warning(
                    #         "Missing obligation level for %s "
                    #         "on company '%s'." % (type, company.name))
                    #     continue
                    intrastat = self.create({
                        'company_id': company.id,
                        'type': type,
                        # 'obligation_level': obligation_level,
                    })
                    logger.info(
                        'An %s Intrastat Product for month %s '
                        'has been created by Odoo for company %s'
                        % (type, previous_month, company.name))
                    try:
                        intrastat.generate_product_lines_from_invoice()
                    except Warning as e:
                        intrastat = intrastat.with_context(
                            exception=True, error_msg=e)
                    # send the reminder e-mail
                    # TODO : how could we translate ${object.type}
                    # in the mail tpl ?
                    intrastat.send_reminder_email(
                        'l10n_es_intrastat_product.'
                        'intrastat_product_reminder_email_template')
        return True


class L10nFrReportIntrastatProductLine(models.Model):
    _name = "l10n.es.report.intrastat.product.line"
    _description = "Intrastat Product Lines for Spain"
    _order = 'id'

    parent_id = fields.Many2one(
        'l10n.es.report.intrastat.product', string='Intrastat Product Ref',
        ondelete='cascade', readonly=True)
    company_id = fields.Many2one(
        'res.company', related='parent_id.company_id', string="Company",
        readonly=True)
    type = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export'),
    ], related='parent_id.type', string="Type", readonly=True)
    company_currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id',
        string="Company currency", readonly=True)
    invoice_id = fields.Many2one(
        'account.invoice', string='Invoice ref', readonly=True)
    quantity = fields.Char(string='Quantity', size=10)
    source_uom_id = fields.Many2one(
        'product.uom', string='Source UoM', readonly=True)
    intrastat_uom_id = fields.Many2one(
        'product.uom', string='Intrastat UoM')
    partner_country_id = fields.Many2one(
        'res.country', string='Partner Country')
    partner_country_code = fields.Char(
        related='partner_country_id.code', string='Partner Country Code',
        readonly=True)
    intrastat_code = fields.Char(string='Intrastat Code', size=9)
    intrastat_code_id = fields.Many2one(
        'hs.code', string='Intrastat Code (not used in XML)')
    # Weight should be an integer... but I want to be able to display
    # nothing in tree view when the value is False (if weight is an
    # integer, a False value would be displayed as 0), that's why weight
    # is a char !
    weight = fields.Char(string='Weight', size=10)
    amount_company_currency = fields.Integer(
        string='Fiscal value in company currency',
        required=True,
        help="Amount in company currency to write in the declaration. "
        "Amount in company currency = amount in invoice currency "
        "converted to company currency with the rate of the invoice date "
        "and rounded at 0 digits")
    amount_invoice_currency = fields.Float(
        string='Fiscal value in invoice currency',
        digits=dp.get_precision('Account'), readonly=True,
        help="Amount in invoice currency = amount of product value in "
        "invoice currency + amount of accessory cost in invoice currency "
        "(not rounded)")
    amount_accessory_cost_inv_cur = fields.Float(
        string='Amount of accessory costs in invoice currency',
        digits=dp.get_precision('Account'), readonly=True,
        help="Amount of accessory costs in invoice currency = total amount "
        "of accessory costs of the invoice broken down into each product "
        "line at the pro-rata of the value")
    amount_product_value_inv_cur = fields.Float(
        string='Amount of product value in invoice currency',
        digits=dp.get_precision('Account'), readonly=True,
        help="Amount of product value in invoice currency ; it is the "
        "amount of the invoice line or group of invoice lines.")
    invoice_currency_id = fields.Many2one(
        'res.currency', string="Invoice Currency", readonly=True)
    product_origin_country_id = fields.Many2one(
        'res.country', string='Product country of origin')
    product_country_origin_code = fields.Char(
        related='product_origin_country_id.code',
        string='Product Country of Origin', readonly=True)
    transport = fields.Selection([
        (1, '1. Transporte marítimo'),
        (2, '2. Transporte por ferrocarril'),
        (3, '3. Transporte por carretera'),
        (4, '4. Transporte aéreo'),
        (5, '5. Envíos postales'),
        (7, '7. Instalaciones fijas de transporte'),
        (8, '8. Transporte de navegación interior'),
        (9, '9. Autopropulsión')
    ], string='Type of transport')
    state = fields.Many2one('res.country.state', string='State')
    intrastat_type_id = fields.Many2one(
        'report.intrastat.type', string='Intrastat Type', required=True)
    is_vat_required = fields.Boolean(
        related='intrastat_type_id.is_vat_required',
        string='Is Partner VAT required ?', readonly=True)
    # Is fiscal_only is not a related fields because,
    # if obligation_level = simplified, is_fiscal_only is always true
    is_fiscal_only = fields.Boolean(
        string='Is fiscal only?', readonly=True)
    procedure_code = fields.Char(
        string='Procedure Code', size=2)
    transaction_code = fields.Char(string='Transaction code', size=2)
    partner_vat = fields.Char(string='Partner VAT', size=32)
    partner_id = fields.Many2one('res.partner', string='Partner Name')
    incoterm_id = fields.Many2one('stock.incoterms', string='Incoterm')
    incoterm_code = fields.Char(
        related='incoterm_id.code',
        string='Icoterm Code')

    @api.one
    @api.constrains('weight', 'quantity')
    def _check_intrastat_line(self):
        if self.weight and not self.weight.isdigit():
            raise ValidationError(_('Weight must be an integer.'))
        if self.quantity and not self.quantity.isdigit():
            raise ValidationError(_('Quantity must be an integer.'))

    # TODO
    # constrains on 'procedure_code', 'transaction_code'

    @api.one
    @api.onchange('partner_id')
    def partner_on_change(self):
        if self.partner_id and self.partner_id.vat:
            self.partner_vat = self.partner_id.vat

    @api.onchange('intrastat_code_id')
    def intrastat_code_on_change(self):
        if self.intrastat_code_id:
            self.intrastat_code = self.intrastat_code_id.intrastat_code
            self.intrastat_uom_id =\
                self.intrastat_code_id.intrastat_uom_id.id or False
        else:
            self.intrastat_code = False
            self.intrastat_uom_id = False

    @api.onchange('intrastat_type_id')
    def intrastat_type_on_change(self):
        # if self.parent_id.obligation_level == 'simplified':
        #     self.is_fiscal_only = True
        if self.intrastat_type_id:
            self.procedure_code = self.intrastat_type_id.procedure_code
            self.transaction_code = self.intrastat_type_id.transaction_code
            self.is_vat_required = self.intrastat_type_id.is_vat_required
            # if self.parent_id.obligation_level == 'detailed':
            #     self.is_fiscal_only = self.intrastat_type_id.is_fiscal_only
        if self.is_fiscal_only:
            self.quantity = False
            self.source_uom_id = False
            self.intrastat_uom_id = False
            self.partner_country_id = False
            self.intrastat_code = False
            self.intrastat_code_id = False
            self.weight = False
            self.product_origin_country_id = False
            self.transport = False
            self.state = False
