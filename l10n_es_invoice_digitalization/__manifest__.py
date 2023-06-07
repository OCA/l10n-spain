# Copyright 2023 Acysos S.L. - Ignacio Ibeas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name":
        "Homologación de software de digitalización certificado de facturas",
    "summary": "l10n_es_invoice_digitalization",
    "version": "15.0.0.1.0",
    "category": "Localization/Spain",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Odoo Community Association (OCA), Acysos S.L.",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
    ],
    "external_dependencies": {
        "python": ["numpy", "cv2", "pytesseract", "Pillow", "io", "scipy"],
    },
    "data": [
        "views/ir_attachment_view.xml",
    ],
}
