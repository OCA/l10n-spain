# Copyright 2009 Alejandro Sanchez <alejandro@asr-oss.com>
# Copyright 2015 Ismael Calvo <ismael.calvo@factorlibre.com>
# Copyright 2015 Tecon
# Copyright 2015 Omar Castiñeira (Comunitea)
# Copyright 2016-2020 Tecnativa - Pedro M. Baeza
# Copyright 2022 Moduon - Eduardo de Miguel
# Copyright 2022 NuoBiT - Eric Antones
# Copyright 2024 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Creación de Facturae",
    "version": "16.0.1.12.1",
    "author": "ASR-OSS, "
    "FactorLibre, "
    "Tecon, "
    "Comunitea, "
    "Tecnativa, "
    "Creu Blanca, "
    "Odoo Community Association (OCA)",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": [
        "account_payment_partner",
        "l10n_es_partner",
        "l10n_es",
        "base_iso3166",
        "base_vat",
        "report_xml",
        "report_qweb_parameter",
        "l10n_es_aeat",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/account_tax_template.xml",
        "views/res_partner_view.xml",
        "views/res_company.xml",
        "views/payment_mode_view.xml",
        "views/account_tax_view.xml",
        "views/report_facturae.xml",
        "wizard/create_facturae_view.xml",
        "wizard/account_move_reversal_view.xml",
        "views/account_move_view.xml",
        "views/account_journal_view.xml",
    ],
    "external_dependencies": {"python": ["pycountry", "xmlsig"]},
    "installable": True,
    "maintainers": ["etobella"],
}
