import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-l10n-spain",
    description="Meta package for oca-l10n-spain Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-l10n_es_account_asset',
        'odoo12-addon-l10n_es_account_bank_statement_import_n43',
        'odoo12-addon-l10n_es_account_banking_sepa_fsdd',
        'odoo12-addon-l10n_es_account_invoice_sequence',
        'odoo12-addon-l10n_es_aeat',
        'odoo12-addon-l10n_es_aeat_mod111',
        'odoo12-addon-l10n_es_aeat_mod115',
        'odoo12-addon-l10n_es_aeat_mod123',
        'odoo12-addon-l10n_es_aeat_mod130',
        'odoo12-addon-l10n_es_aeat_mod216',
        'odoo12-addon-l10n_es_aeat_mod296',
        'odoo12-addon-l10n_es_aeat_mod303',
        'odoo12-addon-l10n_es_aeat_mod347',
        'odoo12-addon-l10n_es_aeat_mod349',
        'odoo12-addon-l10n_es_aeat_mod390',
        'odoo12-addon-l10n_es_aeat_sii',
        'odoo12-addon-l10n_es_dua',
        'odoo12-addon-l10n_es_dua_sii',
        'odoo12-addon-l10n_es_facturae',
        'odoo12-addon-l10n_es_facturae_face',
        'odoo12-addon-l10n_es_irnr',
        'odoo12-addon-l10n_es_location_nuts',
        'odoo12-addon-l10n_es_mis_report',
        'odoo12-addon-l10n_es_partner',
        'odoo12-addon-l10n_es_partner_mercantil',
        'odoo12-addon-l10n_es_pos',
        'odoo12-addon-l10n_es_subcontractor_certificate',
        'odoo12-addon-l10n_es_toponyms',
        'odoo12-addon-l10n_es_vat_book',
        'odoo12-addon-payment_redsys',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
