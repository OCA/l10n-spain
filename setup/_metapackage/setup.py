import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-l10n-spain",
    description="Meta package for oca-l10n-spain Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-delivery_dhl_parcel',
        'odoo14-addon-l10n_es_account_asset',
        'odoo14-addon-l10n_es_account_banking_sepa_fsdd',
        'odoo14-addon-l10n_es_account_statement_import_n43',
        'odoo14-addon-l10n_es_aeat',
        'odoo14-addon-l10n_es_aeat_mod111',
        'odoo14-addon-l10n_es_aeat_mod115',
        'odoo14-addon-l10n_es_aeat_mod123',
        'odoo14-addon-l10n_es_aeat_mod303',
        'odoo14-addon-l10n_es_aeat_mod303_oss',
        'odoo14-addon-l10n_es_aeat_mod347',
        'odoo14-addon-l10n_es_aeat_mod349',
        'odoo14-addon-l10n_es_aeat_mod390',
        'odoo14-addon-l10n_es_aeat_partner_check',
        'odoo14-addon-l10n_es_aeat_sii_oca',
        'odoo14-addon-l10n_es_aeat_sii_oss',
        'odoo14-addon-l10n_es_aeat_vat_prorrate',
        'odoo14-addon-l10n_es_aeat_vat_prorrate_asset',
        'odoo14-addon-l10n_es_dua',
        'odoo14-addon-l10n_es_dua_sii',
        'odoo14-addon-l10n_es_facturae',
        'odoo14-addon-l10n_es_intrastat_report',
        'odoo14-addon-l10n_es_irnr',
        'odoo14-addon-l10n_es_mis_report',
        'odoo14-addon-l10n_es_partner',
        'odoo14-addon-l10n_es_partner_mercantil',
        'odoo14-addon-l10n_es_pos',
        'odoo14-addon-l10n_es_ticketbai',
        'odoo14-addon-l10n_es_ticketbai_api',
        'odoo14-addon-l10n_es_toponyms',
        'odoo14-addon-l10n_es_vat_book',
        'odoo14-addon-l10n_es_vat_book_oss',
        'odoo14-addon-payment_redsys',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
