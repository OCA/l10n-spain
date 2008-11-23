# -*- encoding: utf-8 -*-
{
        "name" : "Comunidades Autónomas de España",
        "version" : "1.0",
        "author" : "Zikzakmedia SL",
        "website" : "http://zikzakmedia.com",
        "category" : "Localisations/Others",
        "description": """Comunidades Autónomas del Estado Español

  * Añade un nuevo campo de comunidades autónomas al formulario de empresas y contactos.
  * Inserta todas las Comunidades Autónomas del Estado Español.
  * Proporciona un assistente para dar de alta las comunidades autónomas por defecto asociadas a los codigos postales. Permite rellenar automaticamente el campo comunidad autónoma del formulario de las empresas y contactos a partir del codigo postal.

Nota: No funciona con el módulo city instalado.""",
        "depends" : ["base"],
        "init_xml" : ["l10n_ES_toponyms_region_data.xml"],
        "demo_xml" : [ ],
        "update_xml" : [
            "l10n_ES_toponyms_region_view.xml",
            "l10n_ES_toponyms_region_wizard.xml",
            "security/ir.model.access.csv",
        ],
        "active": False,
        "installable": True
} 