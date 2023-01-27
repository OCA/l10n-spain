# Copyright 2013 Alberto Martín Cortada (Guadaltech)
# Copyright 2015 AvanzOSC - Ainara Galdona
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# Copyright 2014-2021 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

{
    "name": "AEAT modelo 303",
    "version": "12.0.3.3.0",
    "category": "Accounting",
    "author": "Guadaltech,"
              "AvanzOSC,"
              "Tecnativa,"
              "Eficent,"
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": [
        "l10n_es",
        "l10n_es_aeat",
    ],
    "data": [
        "data/2021-07/aeat.model.export.config.csv",
        "data/2021-07/aeat.model.export.config.line.csv",
        "data/2021-07/l10n.es.aeat.map.tax.csv",
        "data/2021-07/l10n.es.aeat.map.tax.line.csv",
        "data/2022/aeat.model.export.config.csv",
        "data/2022/aeat.model.export.config.line.csv",
        "data/tax_code_map_mod303_data.xml",
        "data/aeat_export_mod303_data.xml",
        "data/aeat_export_mod303_2017_data.xml",
        "data/aeat_export_mod303_2018_data.xml",
        "data/aeat_export_mod303_2021_data.xml",
        "data/l10n.es.aeat.mod303.report.activity.code.csv",
        "views/mod303_view.xml",
        "views/l10n_es_aeat_mod303_report_activity_code_data_views.xml",
        "security/l10n_es_aeat_mod303_security.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
