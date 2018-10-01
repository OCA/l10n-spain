import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo10-addons-oca-l10n-spain",
    description="Meta package for oca-l10n-spain Odoo addons",
    version=version,
    install_requires=[
        'odoo10-addon-account_balance_reporting',
        'odoo10-addon-account_balance_reporting_xlsx',
        'odoo10-addon-l10n_es',
        'odoo10-addon-l10n_es_account_asset',
        'odoo10-addon-l10n_es_account_balance_report',
        'odoo10-addon-l10n_es_account_bank_statement_import_n43',
        'odoo10-addon-l10n_es_account_banking_sepa_fsdd',
        'odoo10-addon-l10n_es_account_fiscal_year_closing',
        'odoo10-addon-l10n_es_account_group',
        'odoo10-addon-l10n_es_account_invoice_sequence',
        'odoo10-addon-l10n_es_aeat',
        'odoo10-addon-l10n_es_aeat_mod111',
        'odoo10-addon-l10n_es_aeat_mod115',
        'odoo10-addon-l10n_es_aeat_mod216',
        'odoo10-addon-l10n_es_aeat_mod296',
        'odoo10-addon-l10n_es_aeat_mod303',
        'odoo10-addon-l10n_es_aeat_mod303_cash_basis',
        'odoo10-addon-l10n_es_aeat_mod349',
        'odoo10-addon-l10n_es_aeat_mod390',
        'odoo10-addon-l10n_es_aeat_sii',
        'odoo10-addon-l10n_es_aeat_sii_cash_basis',
        'odoo10-addon-l10n_es_aeat_vat_prorrate',
        'odoo10-addon-l10n_es_aeat_vat_prorrate_asset',
        'odoo10-addon-l10n_es_crm_lead_trade_name',
        'odoo10-addon-l10n_es_dua',
        'odoo10-addon-l10n_es_dua_sii',
        'odoo10-addon-l10n_es_irnr',
        'odoo10-addon-l10n_es_location_nuts',
        'odoo10-addon-l10n_es_mis_report',
        'odoo10-addon-l10n_es_partner',
        'odoo10-addon-l10n_es_partner_mercantil',
        'odoo10-addon-l10n_es_toponyms',
        'odoo10-addon-l10n_es_vat_book',
        'odoo10-addon-payment_redsys',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
