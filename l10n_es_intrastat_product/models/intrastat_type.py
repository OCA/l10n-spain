# -*- coding: utf-8 -*-
# © 2016 - FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

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
        help="Statistical procedure codes")
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
        string='Transaction code')
    is_fiscal_only = fields.Boolean(
        string='Is fiscal only ?',
        help="Only fiscal data should be provided for this procedure code.")
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
