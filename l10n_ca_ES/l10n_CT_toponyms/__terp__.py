{
		"name" : "Topònims dels Països Catalans",
		"version" : "1.0",
		"author" : "Zikzakmedia SL",
		"website" : "http://zikzakmedia.com",
		"category" : "Localisations/Others",
		"description": """Comarques dels Països Catalans (Catalunya, País Valencià i Illes Balears)

  * Afegeix un nou camp comarca al formulari d'empresa i contacte.
  * Insereix totes les comarques dels Països Catalans associades a cada província.
  * Proporciona un assistent per donar d'alta les comarques per defecte associats als codis postals dels Països Catalans. Permet omplenar automàticament el camp comarca del formulari d'empresa i contacte a partir del codi postal.""",
		"depends" : ["base","l10n_ES_toponyms"],
		"init_xml" : ["l10n_CT_toponyms_data.xml"],
		"demo_xml" : [ ],
		"update_xml" : ["l10n_CT_toponyms_view.xml", "l10n_CT_toponyms_wizard.xml"],
		"active": False,
		"installable": True
} 