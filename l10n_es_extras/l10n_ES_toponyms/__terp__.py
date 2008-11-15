# -*- encoding: utf-8 -*-
{
        "name" : "Topónimos del Estado español",
        "version" : "1.0",
        "author" : "Zikzakmedia SL",
        "website" : "http://zikzakmedia.com",
        "category" : "Localisations/Europe",
        "description": """Provincias, municipios y códigos postales del Estado Español

  * Traduce el país Spain por España
  * Añade las 52 provincias actuales del Estado Español
  * Proporciona un asistente para dar de alta los municipios y provincias por defecto asociados a los 15839 códigos postales del Estado Español. Permite rellenar automáticamente los campos ciudad y provincia del formulario de empresa y contacto a partir del código postal.

Los datos han sido obtenidos de los datos públicos del Instituto Nacional de Estadística (INE).""",
        "depends" : ["base"],
        "init_xml" : ["l10n_ES_toponyms_paises.xml", "l10n_ES_toponyms_provincias.xml", ],
        "demo_xml" : [ ],
        "update_xml" : ["l10n_ES_toponyms_wizard.xml" ],
        "active": False,
        "installable": True
} 