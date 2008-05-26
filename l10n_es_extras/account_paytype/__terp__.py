#!/usr/bin/env python
# -*- coding: utf-8 -*-

{
    "name" : "Account payment type",
    "version" : "1.1",
    "author" : "Pablo Rocandio",
    "category" : "Localisation/Europe",
    "description": """Adds payment type.

A particular payment can have a payment term (30 days, 30/60 days, ...) and a payment type (cash, bank transfer, ...).
This module provides:
	* Definition of payment types. The payment type can have a bank account relation (bank transfer) or no (cash)
	* A default payment type for partners
	* Automatical selection of payment type and bank account in invoices
	* A default check field in partner bank accounts
""",
    "depends" : [
        "base",
        "account",
        ],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
        "account_paytype_view.xml",
        ],
    "active": False,
    "installable": True
}


