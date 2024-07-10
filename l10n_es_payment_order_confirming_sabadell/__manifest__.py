# Copyright 2016 Soluntec Proyectos y Soluciones TIC. - Rubén Francés
# Copyright 2016 Soluntec Proyectos y Soluciones TIC. - Nacho Torró
# Copyright 2015 Tecnativa - Pedro M. Baeza
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Exportación de fichero bancario Confirming para Banco Sabadell",
    "version": "16.0.1.0.1",
    "author": "Soluntec, Odoo Community Association (OCA), Tecnativa",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["account_payment_order"],
    "data": [
        "data/account_payment_method.xml",
        "views/account_payment_mode_view.xml",
    ],
    "installable": True,
}
