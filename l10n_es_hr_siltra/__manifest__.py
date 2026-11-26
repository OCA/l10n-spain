# Copyright 2026 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Importación de Ficheros de SILTRA",
    "summary": """Importa los ficheros de SILTRA para generar las
    ausencias necesarias de forma automática.""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Dixmit,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "depends": [
        "hr_holidays",
    ],
    "data": [
        "views/res_company.xml",
        "security/ir.model.access.csv",
        "views/hr_siltra.xml",
        "views/hr_siltra_item.xml",
    ],
    "demo": [],
}
