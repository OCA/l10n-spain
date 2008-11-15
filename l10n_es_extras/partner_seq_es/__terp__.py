# -*- encoding: utf-8 -*-
{
    "name" : "Partner Sequence",
    "version" : "0.1",
    "author" : "Pablo Rocandio",
    "description": """Este módulo vincula una secuencia al campo de codigo de partner
    """,
    "depends" : ["base","account","l10n_chart_ES","partner_data_es"],
    "init_xml" : [],
    "update_xml" : ['partner_seq_sequence.xml', 'partner_seq_wizard.xml'],
    "active": False,
    "installable": True
}




