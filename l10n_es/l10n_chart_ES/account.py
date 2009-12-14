# -*- encoding: utf-8 -*-

"""
Extensión de los objetos plantilla contable (cuentas, impuestos y otros),
para añadir un campo con el nombre de la plantilla en si (para poder diferenciar
entre PGCE 2008 y PGCE PYMES).
"""

from osv import fields, osv

class account_account_template(osv.osv):
    """Extiende la plantillas de cuentas para añadir el nombre de plantilla"""
    _inherit = "account.account.template"
    _columns = {
        'template_name': fields.char('Template', size=32, select=True),
    }
    #_order = "template_name, code"
account_account_template()

class account_tax_code_template(osv.osv):
    """Extiende la plantillas de códigos de impuestos para añadir el nombre de plantilla"""
    _inherit = 'account.tax.code.template'
    _columns = {
        'template_name': fields.char('Template', size=32, select=True),
    }
    #_order = 'template_name,code,name'
account_tax_code_template()


class account_chart_template(osv.osv):
    """Extiende la plantillas de planes contables para añadir el nombre de plantilla"""
    _inherit="account.chart.template"
    _columns={
        'template_name': fields.char('Template', size=32, select=True),
    }
account_chart_template()


class account_tax_template(osv.osv):
    """Extiende la plantillas de impuestos para añadir el nombre de plantilla"""
    _inherit = 'account.tax.template'
    _columns = {
        'template_name': fields.char('Template', size=32, select=True),
    }
    #_order = 'template_name,sequence'
account_tax_template()


class account_fiscal_position_template(osv.osv):
    """Extiende la plantillas de posiciones fiscales para añadir el nombre de plantilla"""
    _inherit = 'account.fiscal.position.template'
    _columns = {
        'template_name': fields.char('Template', size=32, select=True),
    }
account_fiscal_position_template()


class account_fiscal_position_tax_template(osv.osv):
    """Extiende la plantillas de impuestos de posiciones fiscales para añadir el nombre de plantilla"""
    _inherit = 'account.fiscal.position.tax.template'
    _columns = {
        'template_name': fields.char('Template', size=32, select=True),
    }
account_fiscal_position_tax_template()


class account_fiscal_position_account_template(osv.osv):
    """Extiende la plantillas de cuentas de posiciones fiscales para añadir el nombre de plantilla"""
    _inherit = 'account.fiscal.position.account.template'
    _columns = {
        'template_name': fields.char('Template', size=32, select=True),
    }
account_fiscal_position_account_template()
