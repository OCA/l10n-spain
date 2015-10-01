# -*- encoding: utf-8 -*-
##############################################################################
#
#    Report intrastat product module for OpenERP
#    Copyright (C) 2004-2009 Tiny SPRL (http://tiny.be)
#    Copyright (C) 2010-2014 Akretion (http://www.akretion.com)
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


class ProductUom(models.Model):
    _inherit = "product.uom"

    intrastat_label = fields.Char(
        string='Intrastat Label', size=12,
        help="Label used in the XML file export of the Intrastat "
        "Product Report for this unit of measure.")


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    origin_country_id = fields.Many2one(
        'res.country', string='Country of Origin',
        help="Country of origin of the product "
        "(i.e. product 'made in ____') when purchased from this supplier. "
        "This field is used only when the equivalent field on the product "
        "form is empty.")

    @api.constrains('origin_country_id', 'name', 'product_tmpl_id')
    def _same_supplier_same_origin(self):
        """Products from the same supplier should have the same origin"""
        # Search for same supplier and same product tmpl
        # 'name' on product_supplierinfo is a many2one to res.partner
        same_product_same_suppliers = self.search([
            ('product_tmpl_id', '=', self.product_tmpl_id.id),
            ('name', '=', self.name.id)])
        for supplieri in same_product_same_suppliers:
            if self.origin_country_id != supplieri.origin_country_id:
                raise ValidationError(
                    _("For a particular product, all supplier info "
                        "entries with the same supplier should have the "
                        "same country of origin. But, for product '%s' "
                        "with supplier '%s', there is one entry with "
                        "country of origin '%s' and another entry with "
                        "country of origin '%s'.")
                    % (self.product_tmpl_id.name,
                        self.name.name,
                        self.origin_country_id.name,
                        supplieri.origin_country_id.name))
