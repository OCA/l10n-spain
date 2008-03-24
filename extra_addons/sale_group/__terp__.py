# Autor: Pablo Rocandio

{
    "name" : "Sale Group",
    "version" : "1.0",
    "author" : "Pablo Rocandio",
    "description": """Sale Group
                      This module is usefull if you create manual pickings
                      from sale orders and manual invoices from pickings.
                      It allows to create pickings from selected lines from
                      diferent sale orders and invoices from selected lines 
                      from diferent sales orders""",
    "depends" : ["base", "account", "stock", "sale"],
    "init_xml" : [],
    "update_xml" : [
        'sale_group_view.xml',
        'sale_group_wizard.xml',
        'sale_group_workflow.xml',
                   ],
    "active": False,
    "installable": True
}




