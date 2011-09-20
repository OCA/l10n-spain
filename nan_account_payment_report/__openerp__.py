{
    "name" : "Account Payment Jasper Report", 
    "version" : "1.0",
    "description" : """This module replaces existing report in payment orders.""",
    "author" : "NaN Projectes de Programaril Lliure, S.L.",
    "website" : "http://www.NaN-tic.com",
    "depends" : [ 
        'l10n_es_payment_order',
     ], 
    "category" : "Accounting",
    "demo_xml" : [],
    "init_xml" : [ 
    ],
    "update_xml" : [ 
        'payment_report.xml',
    ],
    "active": False,
    "installable": True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
