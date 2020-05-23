import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-l10n-spain",
    description="Meta package for oca-l10n-spain Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-l10n_es_aeat',
        'odoo13-addon-l10n_es_aeat_mod111',
        'odoo13-addon-l10n_es_mis_report',
        'odoo13-addon-l10n_es_partner',
        'odoo13-addon-l10n_es_pos',
        'odoo13-addon-l10n_es_toponyms',
        'odoo13-addon-payment_redsys',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
