# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "TicketBAI - Batuz - "
            "declaración de todas las operaciones de venta realizadas por las personas "
            "y entidades que desarrollan actividades económicas en Bizkaia",
    "version": "11.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "http://www.binovo.es",
    "author": "Binovo,"
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "auto_install": False,
    "development_status": "Alpha",
    "maintainers": [
        'Binovo'
    ],
    "depends": [
        "l10n_es_ticketbai_api_batuz",
        "l10n_es_ticketbai",
    ],
    "data": [
        "views/account_invoice_views.xml",
        "views/lroe_operation_views.xml"
    ],
}
