{
		"name" : "Topónimos del Estado español",
		"version" : "1.0",
		"author" : "Zikzakmedia SL",
		"website" : "http://zikzakmedia.com",
		"category" : "Localisations/Europe",
		"description": """Provincias, municipios y códigos postales del Estado español.
		
Cambia Spain por España y añade las 52 provincias del Estado español. Mediante un asistente se añaden los valores por defecto de las provincias y municipios referentes a cada código postal. Esto permite rellenar automáticamente los campos ciudad y provincia del formulario contactos a partir del código postal.""",
		"depends" : ["base"],
		"init_xml" : ["l10n_ES_toponyms_paises.xml", "l10n_ES_toponyms_provincias.xml", ],
		"demo_xml" : [ ],
		"update_xml" : ["l10n_ES_toponyms_wizard.xml" ],
		"active": False,
		"installable": True
} 