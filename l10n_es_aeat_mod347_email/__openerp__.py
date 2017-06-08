# -*- coding: utf-8 -*-
# Copyright 2017 Alfredo de la Fuente - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "AEAT 347 model Email",
    "version": "8.0.1.0.0",
    "license": "AGPL-3",
    "author": "AvanzOSC, "
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "contributors": [
        "Jorge Camacho <jcamacho@trey.es>",
        "Ana Juaristi <anajuaristi@avanzosc.es>",
        "Alfredo de la Fuente <alfredodelafuente@avanzosc.es>",
    ],
    "category": "Localisation/Accounting",
    "depends": [
        "l10n_es_aeat_mod347"
    ],
    "data": [
        "views/l10n_es_aeat_mod347_partner_record_view.xml",
        "report/res_partner_mod347_report.xml",
        "data/l10n_es_aeat_mod347_email_data.xml",
    ],
    "installable": True,
}
