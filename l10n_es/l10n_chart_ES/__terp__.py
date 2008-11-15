# -*- encoding: utf-8 -*-
{
    "name" : "Plan general contable 2008 - España",
    "version" : "2.0",
    "author" : "Acysos SL",
    "category" : "Localisation/Account charts",
    "description": """Plan general contable español 2008

* Define el plan general contable 2008
* Incorpora asistente para crear las cuentas con un números de dígitos entre 6 y 8
* Define los siguientes planes de cuentas virtuales:
    * Pérdida y ganancias abreviada
    * Balance abreviado
    * Estado abreviado de ingresos y gastos reconocidos
""",
    "depends" : ["account", "base_vat", "base_iban"],
    "init_xml" : [
        "account_chart.xml",
        "balance_abreviado.xml",
        "eaigr_abreviado.xml",
        "pyg_abreviado.xml"],
    "demo_xml" : [],
    "update_xml" : [
        "l10n_chart_ES_wizard.xml",
#        "l10n_chart_ES_report.xml"
    ],
    "active": False,
    "installable": True
}
