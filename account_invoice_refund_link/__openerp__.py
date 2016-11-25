# -*- coding: utf-8 -*-
# Copyright 2004-2011 Pexego Sistemas Informáticos. (http://pexego.es)
# Copyright 2014 Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Link refund invoice with original",
    "summary": "Link refund invoice with its original invoice",
    "version": "9.0.1.0.0",
    "author": "Spanish Localization Team, "
              "Tecnativa, "
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "contributors": [
        'Pexego <www.pexego.es>',
        'Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>',
        'Antonio Espinosa <antonio.espinosa@tecnativa.com>',
    ],
    "category": "Localisation/Accounting",
    "depends": [
        'account',
    ],
    "data": [
        'views/account_invoice_view.xml',
    ],
    "installable": True,
    "post_init_hook": "post_init_hook",
}
