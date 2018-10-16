import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-l10n-spain",
    description="Meta package for oca-l10n-spain Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-l10n_es_account_bank_statement_import_n43',
        'odoo12-addon-l10n_es_account_invoice_sequence',
        'odoo12-addon-l10n_es_aeat',
        'odoo12-addon-l10n_es_aeat_mod111',
        'odoo12-addon-l10n_es_aeat_mod303',
        'odoo12-addon-l10n_es_partner',
        'odoo12-addon-l10n_es_partner_mercantil',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
