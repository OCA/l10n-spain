#!/usr/bin/env python
# -*- coding: utf-8 -*-

{
    "name" : "Sale Auto-picking",
    "version" : "1.0",
    "author" : "readylan",
    "category" : "Localisation/Europe",
    "description": """This module enables you to process the picking from sale order window using a new button.
    
""",
    "depends" : [
        "sale",
        "stock_valued",
        ],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
        "sale_autopicking_workflow.xml",
        "sale_autopicking_view.xml",
        "sale_autopicking_report.xml",
        ],
    "active": False,
    "installable": True
}


