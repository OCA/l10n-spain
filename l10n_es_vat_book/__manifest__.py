# Copyright 2018 - Praxya
# Copyright 2018 - ForgeFlow
# Copyright 2018 Tecnativa - Luis M. Ontalba
# Copyright 2019 Tecnativa - David Vidal
# Copyright 2020 Creu Blanca - Enric Tobella
# Copyright 2020 Tecnativa - Carlos Daudén
# Copyright 2022 Comunitea - Omar Castiñeira
# Copyright 2018-2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Libro de IVA",
    "version": "16.0.1.4.0",
    "author": "PRAXYA, ForgeFlow, Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": ["l10n_es_aeat", "report_xlsx"],
    "data": [
        "security/ir_rule.xml",
        "security/ir.model.access.csv",
        "data/aeat_vat_book_map_data.xml",
        "views/aeat_vat_book_map_view.xml",
        "views/l10n_es_vat_book.xml",
        "views/l10n_es_vat_book_line.xml",
        "views/l10n_es_vat_book_tax_summary.xml",
        "views/l10n_es_vat_book_summary.xml",
        "report/common_templates.xml",
        "report/report_views.xml",
        "report/vat_book_invoices_issued.xml",
        "report/vat_book_invoices_received.xml",
        "report/vat_book_xlsx.xml",
    ],
    "installable": True,
}
