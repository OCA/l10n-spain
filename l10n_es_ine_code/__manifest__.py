# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "INE codes",
    "summary": "National Statistics Institute codes for Spanish cities",
    "version": "16.0.1.0.0",
    "category": "Localization",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Moval Agroingeniería, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["base", "base_location"],
    "data": [
        "security/ir.model.access.csv",
        "views/ine_code_views.xml",
        "views/res_city_views.xml",
        "views/res_partner_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
