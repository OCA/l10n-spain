# Copyright 2004-2011 Pexego Sistemas Informáticos. (http://pexego.es)
# Copyright 2012 NaN·Tic  (http://www.nan-tic.com)
# Copyright 2013 Acysos (http://www.acysos.com)
# Copyright 2013 Joaquín Pedrosa Gutierrez (http://gutierrezweb.es)
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2016 Tecnativa - Angel Moya <odoo@tecnativa.com>
# Copyright 2018 PESOL - Angel Moya <info@pesol.es>
# Copyright 2014-2022 Tecnativa - Pedro M. Baeza
# Copyright 2014-2032 Binhex - Nicolás Ramos (http://binhex.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Basado en el modelo 347 de la AEAT
{
    "name": "ATC Modelo 415",
    "version": "16.0.1.0.0",
    "author": "Tecnativa,"
    "PESOL,"
    "Binhex System Solutions,"
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Accounting",
    "license": "AGPL-3",
    "depends": [
        "l10n_es_igic",
        "l10n_es_aeat",
        "l10n_es_atc",
    ],
    "data": [
        "data/tax_code_map_mod415_data.xml",
        "security/ir.model.access.csv",
        "security/mod_415_security.xml",
        "views/account_move_view.xml",
        "views/res_partner_view.xml",
        "views/mod415_view.xml",
        "views/report_415_partner.xml",
        "views/mod415_templates.xml",
        "data/mail_template_data.xml",
    ],
    "maintainers": ["nicolasramos"],
    "installable": True,
}
