# -*- coding: utf-8 -*-
# © 2009 Alejandro Sanchez <alejandro@asr-oss.com>
# © 2015 Ismael Calvo <ismael.calvo@factorlibre.com>
# © 2015 Tecon
# © 2015 Juanjo Algaz (MalagaTIC)
# © 2015 Omar Castiñeira (Comunitea)
# © 2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Creación de Factura-e (FACe)",
    "version": "8.0.1.0.0",
    "author": "ASR-OSS, "
              "FactorLibre, "
              "Tecon, "
              "Pexego, "
              "Malagatic, "
              "Comunitea, "
              "Serv. Tecnol. Avanzados - Pedro M. Baeza, "
              "Odoo Community Association (OCA)",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": [
        "account_payment_partner",
        "base_iso3166",
    ],
    "data": [
        "views/res_partner_view.xml",
        "views/res_company.xml",
        "views/payment_mode_view.xml",
        "wizard/create_facturae_view.xml",
    ],
    "installable": True,
}
