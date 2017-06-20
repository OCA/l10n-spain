# -*- coding: utf-8 -*-
# © 2009 Alejandro Sanchez <alejandro@asr-oss.com>
# © 2015 Ismael Calvo <ismael.calvo@factorlibre.com>
# © 2015 Tecon
# © 2015 Omar Castiñeira (Comunitea)
# © 2016 Tecnativa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Creación de Factura-e",
    "version": "10.0.1.0.0",
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
        "account_accountant",
        "l10n_es_partner",
        "l10n_es",
        "base_iso3166",
        "base_vat",
        "partner_firstname",
        "report_xml",
        "report_qweb_parameter",
        "account_banking_mandate"
    ],
    "data": [
        "data/log_counter.xml",
        "data/account_tax_template.xml",
        "security/ir.model.access.csv",
        "views/res_partner_view.xml",
        "views/res_company.xml",
        "views/payment_mode_view.xml",
        "views/account_tax_view.xml",
        "views/report_facturae.xml",
        "wizard/create_facturae_view.xml",
        "wizard/account_invoice_refund_view.xml",
        "wizard/account_invoice_integration_cancel_view.xml",
        "views/account_invoice_integration_view.xml",
        "views/account_invoice_view.xml"
    ],
    "external_dependencies": {
        "python": [
            "OpenSSL",
            "xmlsig"
        ],
    },
    "demo": [
        "demo/integration_method.xml"
    ],
    "installable": True,
}
