# -*- encoding: utf-8 -*-
{
        "name" : "Topónimos del Estado español",
        "version" : "1.0",
        "author" : "Zikzakmedia SL",
        "website" : "http://zikzakmedia.com",
        "category" : "Localisations/Europe",
        "description": """Provincias, municipios y códigos postales del Estado Español

  * Traduce el país Spain por España
  * Añade las 52 provincias actuales del Estado Español con posibilidad de escoger versión oficial, castellana o ambas
  * Proporciona un asistente para dar de alta los municipios y provincias por defecto asociados a los 15839 códigos postales del Estado Español. Permite rellenar automáticamente los campos ciudad y provincia del formulario de empresa y contacto a partir del código postal.
  * Nuevo asistente de configuración que permite crear los valores por defecto según módulo city esté instalado (se crean entidades city.city) o no (se crean valores por defecto de los campos ciudad y provincia asociados al código postal).

Los datos han sido obtenidos de los datos públicos del Instituto Nacional de Estadística (INE).""",
        "depends" : ["base"],
        "init_xml" : ["l10n_ES_toponyms_country.xml", ],
        "demo_xml" : [ ],
        "update_xml" : [
            "l10n_ES_toponyms_wizard.xml",
            "security/ir.model.access.csv",
        ],
        "active": False,
        "installable": True
} 