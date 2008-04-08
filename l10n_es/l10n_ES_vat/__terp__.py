{
		"name" : "Definición impuestos para el Estado Español",
		"version" : "1.0",
		"author" : "Zikzakmedia SL, Acysos SL",
		"website" : "http://tinyerp.com",
		"category" : "Localisations/Accounting & finance",
		"description": """Definición impuestos IVA (IVA 4%, 7%, 16% soportado y 4%, 7%, 16% repercutido) y recargos de equivalencia:

- Definición de los códigos de impuestos para realizar la declaración modelo 300 y 390
- Creación del campo Recargo de Equivalencia en la ficha de Producto y en la de Empresa
- Definición de los 3 recargos de equivalencia IVA05re, IVA1re, IVA4re)
- Definición de los 6 impuestos (IVA4, IVA7, IVA16, 4IVA sopor., 7IVA sopor., 16IVA sopor.)
- Definición de las 6 cuentas contables asociadas (47200004, 47200007, 47200016, 47700004, 47700007, 47700016)
- Definición de la cuenta 47500001, Hacienda acreedora IVA
""",
		"depends" : ["base","account","l10n_sp_2008"],
		"init_xml" : ["l10n_ES_taxes_data.xml"],
		"demo_xml" : [ ],
		"update_xml" : ["partner_view.xml"],
		"installable": True
} 