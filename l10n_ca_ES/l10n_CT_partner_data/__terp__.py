# -*- encoding: utf-8 -*-
{
    "name" : "Dades inicials per al mòdul base",
    "version" : "1.0",
    "author" : "Zikzakmedia SL",
    "website" : "http://www.zikzakmedia.com",
    "category" : "Localisation/Europe",
    "description": """Afegeix dades inicials a les taules:
    * Canals
    * Estats d'ànim
    * Categories d'empreses
    * Càrrecs de contactes
    * Bancs""",
    "depends" : [
        "base",
        ],
    "init_xml" : [
        "data/data_partner_events.xml",     # Canals i estats d'ànim
        "data/data_partner_categories.xml", # Categories d'empreses
        "data/data_partner_functions.xml",  # Càrrecs de contactes
        "data/data_banks.xml",              # Bancs
        ],
    "demo_xml" : [],
    "update_xml" :[],
    "active": False,
    "installable": True
}


