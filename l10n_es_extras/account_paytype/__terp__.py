#!/usr/bin/env python
# -*- coding: utf-8 -*-

{
    "name" : "Account Paytype",
    "version" : "1.1",
    "author" : "Pablo Rocandio",
    "category" : "Localisation/Europe",
    "depends" : [
        "base", 
        "account", 
        "l10n_sp_2008", # Plan General Contable 2008 ACYSOS, S.L.
        "paydays",
        ],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
        "account_paytype_view.xml",
		],
    "active": False,
    "installable": True
}


