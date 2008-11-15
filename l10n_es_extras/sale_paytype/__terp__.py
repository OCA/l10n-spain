# -*- encoding: utf-8 -*-
{
    "name" : "Sale payment type",
    "version" : "1.0",
    "author" : "readylan",
    "category" : "Localisation/Europe",
    "description": """Adds payment type to sale process.

The sale order inherits payment type from business partner as default. Next, the invoice based on this sale order inherits the same information from it.
""",
    "depends" : [
        "account_paytype",
        "sale",
        "stock",
        ],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
        "sale_paytype_view.xml",
        ],
    "active": True,
    "installable": True
}


