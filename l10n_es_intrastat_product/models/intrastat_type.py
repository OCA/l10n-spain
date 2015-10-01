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

from openerp import models, fields


class ReportIntrastatType(models.Model):
    _name = "report.intrastat.type"
    _description = "Intrastat type"
    _order = "procedure_code, transaction_code"

    name = fields.Char(
        string='Name', required=True,
        help="Description of the Intrastat type.")
    active = fields.Boolean(string='Active', default=True)
    object_type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Supplier Invoice'),
        ('out_refund', 'Customer Refund'),
        ('in_refund', 'Supplier Refund')
    ], string='Possible on', select=True, required=True)
    procedure_code = fields.Selection([
        ('1', '1 - Llegada/Salida de mercancías con destino final'),
        ('2', '2 - Llegada/Salida temporal de mercancías para ser '
            'reexpedidas/reintroducidas con posterioridad en el mismo estado'),
        ('3', '2 - Llegada/Salida temporal de mercancías para ser '
            'reexpedidas/reintroducidas con posterioridad, después de haber '
            'sido reparas o transformadas'),
        ('4', '4 - Llegada/Salida de mercancías devueltas en el mismo estado'),
        ('5', '5 - Llegada/Salida de mercancías devueltas después de haber '
            'haber sido reparas o transformadas')],
        string='Procedure code', required=True,
        help="For the 'DEB' declaration to France's customs "
        "administration, you should enter the 'code régime' here.")
    transaction_code = fields.Selection([
        ('11', '11 - Compra/venta en firme'),
        ('12', '12 - Suministro para la venta salvo aprobación o de prueba, '
            'para consignación o con la mediación de un agente comisionado '),
        ('13', '13 - Trueque (compensación en especie)'),
        ('14', '14 - Compras por particulares'),
        ('15', '15 - Arrendamiento financiero (alquiler-compra)'),
        ('21', '21 - Devolución de mercancías'),
        ('22', '22 - Sustitución de mercancías devueltas'),
        ('23', '23 - Sustitución (por ejemplo, bajo garantía) '
            'de mercancías no devueltas'),
        ('31', '31 - Mercancías entregadas en el marco de programas de ayuda '
            'gestionados o financiados parcial o totalmente por la Comunidad '
            'Europea'),
        ('32', '32 - Otras entregas de ayuda gubernamental '),
        ('33', '33 - Otras entregas de ayuda (particulares, '
            'organizaciones no gubernamentales) '),
        ('34', '34 - Otros '),
        ('40', '40 - Operaciones con miras al trabajo por encargo (excepto '
            'las que se registren en el epígrafe 7)'),
        ('50', '50 - Operaciones tras el trabajo por encargo (excepto las que '
            'se registren en el epígrafe 7) '),
        ('70', '70 - Operaciones en el marco de programas comunes de defensa '
            'u otros programas intergubernamentales de producción conjunta '),
        ('80', '80 - Suministro de materiales de construcción y maquinaria '
            'para trabajos en el marco de un contrato general de construcción '
            'o ingeniería'),
        ('90', '90 - Otras transacciones')],
        string='Transaction code',
        help="For the 'DEB' declaration to France's customs "
        "administration, you should enter the number 'nature de la "
        "transaction' here.")
    is_fiscal_only = fields.Boolean(
        string='Is fiscal only ?',
        help="Only fiscal data should be provided for this procedure code.")
    fiscal_value_multiplier = fields.Integer(
        string='Fiscal value multiplier', default=1,
        help="'0' for procedure codes 19 and 29, "
        "'-1' for procedure code 25, '1' for all the others. "
        "This multiplier is used to compute the total fiscal value of "
        "the declaration.")
    is_vat_required = fields.Boolean(
        string='Is partner VAT required?',
        help="True for all procedure codes except 11, 19 and 29. "
        "When False, the VAT number should not be filled in the "
        "Intrastat product line.")
    intrastat_product_type = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export')],
        string='Intrastat product type',
        help="Decides on which kind of Intrastat product report "
        "('Import' or 'Export') this Intrastat type can be selected.")

    _sql_constraints = [(
        'code_invoice_type_uniq',
        'unique(procedure_code, transaction_code, intrastat_product_type)',
        'The group (procedure code, transaction code, intrastat_product_type) '
        'must be unique.'
    )]
