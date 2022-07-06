# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Envío de Factura-e a FACe",
    "version": "15.0.1.1.1",
    "author": "Creu Blanca, " "Odoo Community Association (OCA)",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": [
        "l10n_es_facturae",
        "edi_webservice_oca",
        "edi_account_oca",
        "edi_exchange_template_oca",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/edi.xml",
        "data/face_data.xml",
        "data/edi_output.xml",
        "wizards/edi_l10n_es_facturae_face_cancel.xml",
        "views/account_move.xml",
        "views/res_company_view.xml",
        "views/res_partner.xml",
        "views/res_config_views.xml",
        "views/edi_exchange_record.xml",
    ],
    "external_dependencies": {"python": ["OpenSSL", "zeep", "cryptography"]},
    "installable": True,
    "maintainers": ["etobella"],
}
