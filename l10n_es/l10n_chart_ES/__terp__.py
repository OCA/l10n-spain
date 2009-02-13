# -*- encoding: utf-8 -*-
{
    "name" : "Spain - New Chart of Accounts 2008",
    "version" : "2.0",
    "author" : "Spanish Localization Team",
    "category" : "Localisation/Account Charts",
    "description": """Nuevo plan general contable español 2008

* Define la plantilla del plan general contable 2008
* Define la plantilla de los impuestos IVA soportado, IVA repercutido, recargos de equivalencia
* Define la plantilla de códigos de impuestos
""",
    "depends" : ["account", "base_vat", "base_iban"],
    "init_xml" : [
    "account_chart.xml",
	"taxes_data.xml",
    "fiscal_templates.xml"
        ],
    "demo_xml" : [],
    "update_xml" : [
#        "l10n_chart_ES_wizard.xml",
#        "l10n_chart_ES_report.xml"
    ],
    "active": False,
    "installable": True
}
