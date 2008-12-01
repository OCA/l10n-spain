# -*- encoding: utf-8 -*-
{
    "name" : "Secuencia empresa",
    "version" : "0.1",
    "author" : "Pablo Rocandio y Zikzakmedia SL",
    "description": """Este módulo:
  * Vincula una secuencia al campo de código de empresa para generar el código de forma automática (sólo al crear nuevas empresas clientes o proveedores).
  * Añade un asistente para crear las cuentas a pagar y a cobrar de la empresa según su código (si no tuviera código se crea uno según la secuencia).
La secuencia de empresa por defecto se inicia en NP00101 (prefijo NP y relleno de 5 dígitos) y puede modificarse posteriormente en Administración/Personalización/Secuencias. La longitud de los códigos de las cuentas a pagar/cobrar creadas dependerá del relleno del número de la secuencia. Si, por ejemplo, el relleno es de 5 dígitos, las cuentas creadas serán de 8 dígitos pues se añade 400 o 430 delante: 40000101, 43000101, ...
    """,
    "depends" : ["base","account","l10n_chart_ES",],
    "init_xml" : [],
    "update_xml" : [
        "partner_seq_sequence.xml",
        "partner_seq_wizard.xml"
        ],
    "active": False,
    "installable": True
}




