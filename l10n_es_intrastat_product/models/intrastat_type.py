# -*- encoding: utf-8 -*-
##############################################################################
#
#    l10n Spain Report intrastat product module for Odoo
#    Copyright (C) 2010-2014 Akretion (http://www.akretion.com/)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
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
from openerp.exceptions import ValidationError

# If you modify the line below, please also update intrastat_type_view.xml
# (form view of report.intrastat.type, field transaction_code
fiscal_only_tuple = ('25', '26', '31')


class ReportIntrastatType(models.Model):
    _name = "report.intrastat.type"
    _description = "Intrastat type"
    _order = "procedure_code, transaction_code"

    @api.one
    @api.depends('procedure_code')
    def _compute_all(self):
        if self.procedure_code in ('19', '29'):
            self.fiscal_value_multiplier = 0
        elif self.procedure_code == '25':
            self.fiscal_value_multiplier = -1
        else:
            self.fiscal_value_multiplier = 1
        if self.procedure_code in fiscal_only_tuple:
            self.is_fiscal_only = True
        else:
            self.is_fiscal_only = False
        if self.procedure_code in ('11', '19', '29'):
            self.is_vat_required = False
        else:
            self.is_vat_required = True
        if self.procedure_code in ('11', '19'):
            self.intrastat_product_type = 'import'
        else:
            self.intrastat_product_type = 'export'

    name = fields.Char(
        string='Name', required=True,
        help="Description of the Intrastat type.")
    active = fields.Boolean(string='Active', default=True)
    object_type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Supplier Invoice'),
        ('out_refund', 'Customer Refund'),
        ('none', 'None'),
    ], string='Possible on', select=True, required=True)
    procedure_code = fields.Selection([
        ('11', "11. Acquisitions intracomm. taxables en France"),
        ('19', "19. Autres introductions"),
        ('21', "21. Livraisons intracomm. exo. en France et taxables "
            "dans l'Etat d'arrivée"),
        ('25', "25. Régularisation commerciale - minoration de valeur"),
        ('26', "26. Régularisation commerciale - majoration de valeur"),
        ('29', "29. Autres expéditions intracomm. : travail à façon, "
            "réparation..."),
        ('31', "31. Refacturation dans le cadre d'une opération "
            "triangulaire")
    ], string='Procedure code', required=True,
        help="For the 'DEB' declaration to France's customs "
        "administration, you should enter the 'code régime' here.")
    transaction_code = fields.Selection([
        ('', '-'),
        ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'),
        ('19', '19'),
        ('21', '21'), ('22', '22'), ('23', '23'), ('29', '29'),
        ('30', '30'),
        ('41', '41'), ('42', '42'),
        ('51', '51'), ('52', '52'),
        ('70', '70'),
        ('80', '80'),
        ('91', '91'), ('99', '99'),
    ], string='Transaction code',
        help="For the 'DEB' declaration to France's customs "
        "administration, you should enter the number 'nature de la "
        "transaction' here.")
    is_fiscal_only = fields.Boolean(
        compute='_compute_all', string='Is fiscal only ?', store=True,
        readonly=True,
        help="Only fiscal data should be provided for this procedure code.")
    fiscal_value_multiplier = fields.Integer(
        compute='_compute_all', string='Fiscal value multiplier', store=True,
        readonly=True,
        help="'0' for procedure codes 19 and 29, "
        "'-1' for procedure code 25, '1' for all the others. "
        "This multiplier is used to compute the total fiscal value of "
        "the declaration.")
    is_vat_required = fields.Boolean(
        compute='_compute_all', string='Is partner VAT required?', store=True,
        readonly=True,
        help="True for all procedure codes except 11, 19 and 29. "
        "When False, the VAT number should not be filled in the "
        "Intrastat product line.")
    intrastat_product_type = fields.Char(
        compute='_compute_all', string='Intrastat product type', store=True,
        readonly=True,
        help="Decides on which kind of Intrastat product report "
        "('Import' or 'Export') this Intrastat type can be selected.")

    _sql_constraints = [(
        'code_invoice_type_uniq',
        'unique(procedure_code, transaction_code)',
        'The pair (procedure code, transaction code) must be unique.'
    )]

    @api.one
    @api.constrains('procedure_code', 'transaction_code')
    def _code_check(self):
        if self.object_type == 'out' and self.procedure_code != '29':
            raise ValidationError(
                _("Procedure code must be '29' for an Outgoing products."))
        elif self.object_type == 'in' and self.procedure_code != '19':
            raise ValidationError(
                _("Procedure code must be '19' for an Incoming products."))
        if (
                self.procedure_code not in fiscal_only_tuple
                and not self.transaction_code):
            raise ValidationError(
                _('You must enter a value for the transaction code.'))
        if (
                self.procedure_code in fiscal_only_tuple
                and self.transaction_code):
            raise ValidationError(
                _("You should not set a transaction code when the "
                    "Procedure code is '25', '26' or '31'."))

    @api.onchange('procedure_code')
    def procedure_code_on_change(self):
        if self.procedure_code in fiscal_only_tuple:
            self.transaction_code = False
