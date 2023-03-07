# Copyright (C) 2022 Trey, Kilobytes de Soluciones - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Datos extra para el SII",
    "summary": "Módulo para incluir los impuestos extra en el módulo del SII.",
    "author": "Trey (www.trey.es), Odoo Community Association (OCA)",
    "maintainers": [
        "cubells",
    ],
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "category": "Accounting & Finance",
    "version": "11.0.1.1.0",
    "depends": [
        "l10n_es_aeat_sii",
        "l10n_es_extra_data",
    ],
    "data": [
        "data/aeat_sii_map_data.xml",
    ],
    "installable": True,
    "autoinstall": True,
}
