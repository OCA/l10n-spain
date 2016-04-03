# -*- coding: utf-8 -*-
# © 2011 NaN Projectes de Programari Lliure, S.L.
# © 2013-2016 Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Secuencia para facturas separada de la secuencia de asientos",
    "version": "8.0.1.3.0",
    "author": "Spanish Localization Team, "
              "NaN·Tic, "
              "Trey, "
              "Serv. Tecnol. Avanzados - Pedro M. Baeza, "
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Accounting",
    "license": "AGPL-3",
    "depends": [
        'l10n_es',
    ],
    "data": [
        'data/sequence_data.xml',
        'views/account_view.xml',
    ],
    "post_init_hook": "fill_invoice_sequences",
    "installable": True,
}
