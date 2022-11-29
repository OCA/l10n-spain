# Copyright 2004-2011 Luis Manuel Angueira Blanco - Pexego
# Copyright 2013-2019 Ignacio Ibeas - Acysos S.L. (http://acysos.com)
# Copyright 2015 Ainara Galdona <agaldona@avanzosc.com>
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2018 Juan Vicente Pascual <jvpascual@puntsistemes.es>
# Copyright 2019 Tecnativa - Carlos Dauden
# Copyright 2013-2021 Tecnativa - Pedro M. Baeza
# Copyright 2022 Moduon - Eduardo de Miguel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

{
    "name": "AEAT Base",
    "summary": "Modulo base para declaraciones de la AEAT",
    "version": "14.0.2.4.1",
    "author": "Pexego, "
    "Acysos S.L., "
    "AvanzOSC, "
    "Tecnativa, "
    "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Accounting & Finance",
    "development_status": "Mature",
    "depends": ["l10n_es", "account_tax_balance"],
    "external_dependencies": {"python": ["unidecode", "cryptography"]},
    "data": [
        "security/aeat_security.xml",
        "security/ir.model.access.csv",
        "data/aeat_partner.xml",
        "data/ir_config_parameter.xml",
        "data/aeat_tax_agency_data.xml",
        "wizard/export_to_boe_wizard.xml",
        "wizard/compare_boe_file_views.xml",
        "wizard/aeat_certificate_password_view.xml",
        "views/aeat_menuitem.xml",
        "views/aeat_report_view.xml",
        "views/aeat_tax_agency_view.xml",
        "views/aeat_tax_line_view.xml",
        "views/aeat_export_configuration_view.xml",
        "views/aeat_tax_code_mapping_view.xml",
        "views/account_move_line_view.xml",
        "views/res_company_view.xml",
        "views/res_partner_view.xml",
        "views/aeat_certificate_view.xml",
        "views/account_journal_view.xml",
        "views/account_move_view.xml",
    ],
    "installable": True,
    "maintainers": ["pedrobaeza"],
}
