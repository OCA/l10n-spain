# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Spanish TGSS fields for partners",
    "summary": "Add fields needed to interact with TGSS to partners",
    "version": "8.0.1.0.0",
    "category": "Customer Relationship Management",
    "website": "https://grupoesoc.es/",
    "author": u"Grupo ESOC Ingeniería de servicios, S.L., "
              u"Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account",
        "base_vat",
        "l10n_es_tgss",
        "partner_contact_personal_information_page",
    ],
    "data": [
        "views/res_partner.xml",
    ],
}
