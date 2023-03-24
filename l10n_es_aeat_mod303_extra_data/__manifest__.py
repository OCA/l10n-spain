# Copyright (C) 2022 Trey, Kilobytes de Soluciones - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "AEAT modelo 303 - Datos extra",
    "summary": "Módulo para incluir los impuestos extra en el modelo 303.",
    "author": "Trey (www.trey.es), Odoo Community Association (OCA)",
    "maintainers": [
        "cubells",
    ],
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "category": "Accounting & Finance",
    "version": "12.0.2.0.0",
    "depends": [
        "l10n_es_aeat_mod303",
        "l10n_es_extra_data",
    ],
    "data": [
        "data/l10n_es_aeat_map_tax_line.xml",
        "data/2023/l10n_es_aeat_map_tax_line.xml",
    ],
    "autoinstall": True,
}
