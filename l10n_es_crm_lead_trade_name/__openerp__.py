# -*- coding: utf-8 -*-
# © 2015 Antiun Ingeniería, S.L.
# © 2017 QubiQ 2010, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Trade name in leads",
    "summary": "Add trade name field to leads",
    "version": "9.0.1.0.0",
    "category": "Customer Relationship Management",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Antiun Ingeniería S.L.,"
              "QubiQ 2010,"
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    'installable': True,
    "depends": [
        "crm",
        "l10n_es_partner",
    ],
    "data": [
        "views/crm_lead.xml",
    ],
}
