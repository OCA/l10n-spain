{
    "name" : "Stock valued",
    "version" : "0.3",
    "author" : "Pablo Rocandio y ACYSOS, S.L.",
    "description": """Albaranes valorados
    """,
    "depends" : ["base", "account", "stock", "sale"],
    "init_xml" : [],
    "update_xml" : [
        'stock_valued_view.xml',
        'stock_valued_report.xml',
                   ],
    "installable": True
}




