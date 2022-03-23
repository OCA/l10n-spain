# -*- coding: utf-8 -*-
# © 2013 Alberto Martín Cortada (Guadaltech)
# © 2014-2015 Pedro M. Baeza
# © 2015 AvanzOSC - Ainara Galdona
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

{
    "name": "AEAT modelo 303",
    "version": "8.0.3.2.0",
    'category': "Accounting & Finance",
    'author': "Guadaltech,"
              "AvanzOSC,"
              "Serv. Tecnol. Avanzados - Pedro M. Baeza,"
              "Antiun Ingeniería S.L.,"
              "Comunitea,"
              "Odoo Community Association (OCA),"
              "Otherway Creatives S.L.",
    'website': "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": [
        "l10n_es",
        "l10n_es_aeat",
    ],
    "data": [
        "data/202107/aeat.model.export.config.csv",
        "data/202107/aeat.model.export.config.line.csv",
        "data/202107/aeat.mod.map.tax.code.csv",
        "data/202107/aeat.mod.map.tax.code.line.csv",
        "data/2022/aeat.model.export.config.csv",
        "data/2022/aeat.model.export.config.line.csv",
        "data/tax_code_map_mod303_data.xml",
        "data/aeat_export_mod303_data.xml",
        "data/aeat_export_mod303_2017_data.xml",
        "data/aeat_export_mod303_2018_data.xml",
        "data/aeat_export_mod303_2021_data.xml",
        "data/l10n_es_aeat_mod303_report_activity_code_data.xml",
        "views/mod303_view.xml",
        "views/l10n_es_aeat_mod303_report_activity_code_data_views.xml",
        "security/ir.model.access.csv",
        "security/ir_rule.xml"
    ],
    "installable": True,
}
