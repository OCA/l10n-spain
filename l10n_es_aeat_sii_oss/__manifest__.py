# Copyright 2021 FactorLibre - Rodrigo Bonilla <rodrigo.bonilla@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Suministro Inmediato de Información en el IVA: OSS",
    "version": "16.0.2.0.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "FactorLibre, Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "autoinstall": True,
    "development_status": "Production/Stable",
    "maintainers": ["pedrobaeza"],
    "depends": [
        "l10n_es_aeat_sii_oca",
        "account_fiscal_position_partner_type",
        "l10n_eu_oss_oca",
    ],
    "data": ["data/aeat_sii_mapping_registration_keys_data.xml"],
}
