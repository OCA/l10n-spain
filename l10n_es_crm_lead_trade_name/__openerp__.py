# -*- coding: utf-8 -*-
# © 2015 Antiun Ingeniería, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Trade name in leads",
    "summary": "Add trade name field to leads",
    "version": "8.0.1.0.0",
    "category": "Customer Relationship Management",
    "website": "http://www.antiun.com",
    "author": "Antiun Ingeniería S.L., Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "crm",
        "l10n_es_partner",
    ],
    "data": [
        "views/crm_lead.xml",
    ],
}
