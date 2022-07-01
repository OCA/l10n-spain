import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-l10n-spain",
    description="Meta package for oca-l10n-spain Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-l10n_es_account_asset>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_account_banking_sepa_fsdd>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_account_statement_import_n43>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_aeat>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_aeat_mod111>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_aeat_mod115>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_aeat_mod123>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_aeat_mod303>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_aeat_mod303_oss>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_aeat_mod347>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_aeat_mod349>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_aeat_mod390>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_aeat_mod390_oss>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_aeat_partner_check>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_aeat_sii_oca>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_aeat_sii_oss>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_dua>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_dua_sii>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_facturae>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_facturae_face>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_irnr>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_mis_report>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_partner>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_partner_mercantil>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_pos>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_ticketbai>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_ticketbai_api>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_toponyms>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_vat_book>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_vat_book_oss>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
