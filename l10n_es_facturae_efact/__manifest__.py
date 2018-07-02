# © 2015 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Envío de Factura-e a e.FACT",
    "version": "11.0.1.0.0",
    "author": "Creu Blanca, "
              "Odoo Community Association (OCA)",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": [
        "l10n_es_facturae",
    ],
    "data": [
        "data/efact_data.xml",
        "views/res_partner_view.xml",
        "views/account_invoice_integration_view.xml",
        "views/res_config_views.xml",
        "views/res_company_view.xml",
    ],
    "external_dependencies": {
        "python": [
            "paramiko",
            "OpenSSL",
            "xmlsec"
        ]
    },
    "installable": True,
}
