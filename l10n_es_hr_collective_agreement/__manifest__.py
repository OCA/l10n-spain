# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "L10n ES Hr Collective Agreement",
    "summary": "Datos iniciales de configuración para convenios colectivos en España",
    "version": "18.0.1.0.0",
    "category": "Localization/Spain",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Sygel Technology S.L., Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "hr_collective_agreement",
    ],
    "data": [
        "data/collective_agreement_scope_data.xml",
        "data/collective_agreement_official_publication_data.xml",
    ],
}
