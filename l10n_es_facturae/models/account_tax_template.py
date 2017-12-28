# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountTaxTemplate(models.Model):
    _inherit = "account.tax.template"

    facturae_code = fields.Selection(
        selection=[
            ('01', 'IVA: Impuesto sobre el valor añadido'),
            ('02', 'IPSI: Impuesto sobre la producción, los servicios y'
                   ' la importación'),
            ('03', 'IGIC: Impuesto general indirecto de Canarias'),
            ('04', 'IRPF: Impuesto sobre la Renta de las personas físicas'),
            ('05', 'Otro'),
            ('06', 'ITPAJD: Impuesto sobre transmisiones patrimoniales y'
                   ' actos jurídicos documentados'),
            ('07', 'IE: Impuestos especiales'),
            ('08', 'Ra: Renta aduanas'),
            ('09', 'IGTECM: Impuesto general sobre el tráfico de empresas que'
                   ' se aplica en Ceuta y Melilla'),
            ('10', 'IECDPCAC: Impuesto especial sobre los combustibles'
                   ' derivados del petróleo en la Comunidad Autonoma Canaria'),
            ('11', 'IIIMAB: Impuesto sobre las instalaciones que inciden sobre'
                   ' el medio ambiente en la Baleares'),
            ('12', 'ICIO: Impuesto sobre las construcciones, instalaciones y'
                   ' obras'),
            ('13', 'IMVDN: Impuesto municipal sobre las viviendas desocupadas'
                   ' en Navarra'),
            ('14', 'IMSN: Impuesto municipal sobre solares en Navarra'),
            ('15', 'IMGSN: Impuesto municipal sobre gastos suntuarios en'
                   ' Navarra'),
            ('16', 'IMPN: Impuesto municipal sobre publicidad en Navarra'),
            ('17', 'REIVA: Régimen especial de IVA para agencias de viajes'),
            ('18', 'REIGIC: Régimen especial de IGIC: para agencias de'
                   'viajes'),
            ('19', 'REIPSI: Régimen especial de IPSI para agencias de viajes'),
        ], string='Facturae code'
    )

    def _get_tax_vals(self, company, tax_template_to_tax):
        val = super(AccountTaxTemplate, self)._get_tax_vals(
            company, tax_template_to_tax)
        val['facturae_code'] = self.facturae_code
        return val
