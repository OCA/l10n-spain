{
	"name" : "Informes de balances contables para España",
	"version" : "1.0",
	"depends" : ["account","l10n_chart_ES"],
	"author" : "Tiny, Acysos SL, Zikzakmedia SL",
	"description": """Informes de balances contables para España:

* Pérdidas y ganancias
* Balance abreviado de situación
* Estado abreviado de ingresos y gastos""",
	"category" : "Generic Modules/Accounting",
	"init_xml" : [ ],
	"demo_xml" : [ ],
	"update_xml" : [
		"account_view.xml",
		"account_report.xml",
		"account_data.xml",
		"account_report_ES.xml",
	],
	"active": False,
	"installable": True
}
