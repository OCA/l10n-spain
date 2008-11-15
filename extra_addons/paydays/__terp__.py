# -*- encoding: utf-8 -*-
{
    "name" : "Paydays",
    "version" : "1.0",
    "author" : "ACYSOS, S.L. y Pablo Rocandio",
    "description": """Este módulo permite definir los días de pago.

En el campo días de pago del formulario de partners se introducen los días de pago separados por cualquier carácter no numérico. El módulo convierte los días de pago a un formato separado por guiones (por ejemplo 5-15-25).""",
    "depends" : ["base", "account"],
    "init_xml" : [],
    "update_xml" : ['paydays_view.xml',],
    "active": False,
    "installable": True
}




