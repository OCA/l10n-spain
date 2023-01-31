# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "TicketBAI (API) - Batuz - "
            "declaración de todas las operaciones de venta realizadas por las personas "
            " y entidades que desarrollan actividades económicas en Bizkaia",
    "version": "12.0.1.1.3",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Binovo,"
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "auto_install": False,
    "development_status": "Alpha",
    "maintainers": [
        "ao-landoo",
    ],
    "depends": [
        "l10n_es_ticketbai_api",
    ],
    "external_dependencies": {
        "python": [
            "xmltodict",
            "requests_pkcs12"
        ],
    },
    "data": [
        "security/ir.model.access.csv",
        "data/tax_agency_data.xml",
        "data/lroe_chapter_data.xml",
        "views/res_company_views.xml",
        "views/lroe_operation_views.xml"
    ],
}
