import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo11-addons-oca-l10n-spain",
    description="Meta package for oca-l10n-spain Odoo addons",
    version=version,
    install_requires=[
        'odoo11-addon-l10n_es_account_asset',
        'odoo11-addon-l10n_es_account_bank_statement_import_n43',
        'odoo11-addon-l10n_es_account_banking_sepa_fsdd',
        'odoo11-addon-l10n_es_account_invoice_sequence',
        'odoo11-addon-l10n_es_aeat',
        'odoo11-addon-l10n_es_aeat_mod111',
        'odoo11-addon-l10n_es_aeat_mod115',
        'odoo11-addon-l10n_es_aeat_mod123',
        'odoo11-addon-l10n_es_aeat_mod303',
        'odoo11-addon-l10n_es_aeat_mod347',
        'odoo11-addon-l10n_es_aeat_mod349',
        'odoo11-addon-l10n_es_aeat_mod390',
        'odoo11-addon-l10n_es_aeat_sii',
        'odoo11-addon-l10n_es_dua',
        'odoo11-addon-l10n_es_facturae',
        'odoo11-addon-l10n_es_facturae_efact',
        'odoo11-addon-l10n_es_facturae_face',
        'odoo11-addon-l10n_es_location_nuts',
        'odoo11-addon-l10n_es_mis_report',
        'odoo11-addon-l10n_es_partner',
        'odoo11-addon-l10n_es_partner_mercantil',
        'odoo11-addon-l10n_es_pos',
        'odoo11-addon-l10n_es_toponyms',
        'odoo11-addon-l10n_es_vat_book',
        'odoo11-addon-payment_redsys',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
