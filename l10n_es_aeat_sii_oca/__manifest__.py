# Copyright 2017 Acysos - Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2017 Diagram Software S.L.
# Copyright 2017 MINORISA - <ramon.guiu@minorisa.net>
# Copyright 2017 Studio73 - Pablo Fuentes <pablo@studio73.es>
# Copyright 2017 Studio73 - Jordi Tolsà <jordi@studio73.es>
# Copyright 2017 Factor Libre - Ismael Calvo
# Copyright 2017 Otherway - Pedro Rodríguez Gil
# Copyright 2018 Javi Melendez <javimelex@gmail.com>
# Copyright 2018 Angel Moya <angel.moya@pesol.es>
# Copyright 2020 Sygel Technology - Valentín Vinagre <valentin.vinagre@sygel.es>
# Copyright 2021 Tecnativa - João Marques
# Copyright 2022 ForgeFlow - Lois Rilo
# Copyright 2022-2023 Moduon - Eduardo de Miguel
# Copyright 2017-2023 Tecnativa - Pedro M. Baeza
# Copyright 2023 Aures Tic - Jose Zambudio <jose@aurestic.es>
# Copyright 2023 Pol Reig <pol.reig@qubiq.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Suministro Inmediato de Información en el IVA",
    "version": "16.0.1.8.1",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Acysos S.L.,"
    "Diagram,"
    "Minorisa,"
    "Studio73,"
    "FactorLibre,"
    "Comunitea,"
    "Otherway,"
    "Tecnativa,"
    "Javi Melendez,"
    "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["pedrobaeza"],
    "external_dependencies": {"python": ["zeep", "requests"]},
    "depends": [
        "account_invoice_refund_link",
        "l10n_es",
        "l10n_es_aeat",
        "queue_job",
    ],
    "data": [
        "data/aeat_sii_queue_job.xml",
        "data/aeat_sii_tax_agency_data.xml",
        "views/res_company_view.xml",
        "views/account_move_views.xml",
        "wizards/account_move_reversal_views.xml",
        "wizards/account_move_send_sii_views.xml",
        "views/aeat_sii_mapping_registration_keys_view.xml",
        "data/aeat_sii_mapping_registration_keys_data.xml",
        "views/aeat_sii_map_view.xml",
        "data/aeat_sii_map_data.xml",
        "security/ir.model.access.csv",
        "security/aeat_sii.xml",
        "views/product_view.xml",
        "views/queue_job_views.xml",
        "views/account_fiscal_position_view.xml",
        "views/res_partner_views.xml",
        "views/aeat_tax_agency_view.xml",
        "views/account_journal_view.xml",
    ],
    "images": ["static/description/SII_1.jpg"],
    "post_init_hook": "add_key_to_existing_invoices",
}
