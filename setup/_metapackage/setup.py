import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-l10n-spain",
    description="Meta package for oca-l10n-spain Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-l10n_es_account_statement_import_n43',
        'odoo14-addon-l10n_es_aeat',
        'odoo14-addon-l10n_es_aeat_mod111',
        'odoo14-addon-l10n_es_aeat_mod303',
        'odoo14-addon-l10n_es_aeat_mod390',
        'odoo14-addon-l10n_es_dua',
        'odoo14-addon-l10n_es_partner',
        'odoo14-addon-l10n_es_partner_mercantil',
        'odoo14-addon-l10n_es_toponyms',
        'odoo14-addon-l10n_es_vat_book',
        'odoo14-addon-payment_redsys',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
