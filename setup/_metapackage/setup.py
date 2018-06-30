import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo9-addons-oca-l10n-spain",
    description="Meta package for oca-l10n-spain Odoo addons",
    version=version,
    install_requires=[
        'odoo9-addon-account_balance_reporting',
        'odoo9-addon-l10n_es',
        'odoo9-addon-l10n_es_account_asset',
        'odoo9-addon-l10n_es_account_balance_report',
        'odoo9-addon-l10n_es_account_bank_statement_import_n43',
        'odoo9-addon-l10n_es_account_fiscal_year_closing',
        'odoo9-addon-l10n_es_account_invoice_sequence',
        'odoo9-addon-l10n_es_aeat',
        'odoo9-addon-l10n_es_aeat_mod111',
        'odoo9-addon-l10n_es_aeat_mod115',
        'odoo9-addon-l10n_es_aeat_mod216',
        'odoo9-addon-l10n_es_aeat_mod296',
        'odoo9-addon-l10n_es_aeat_mod303',
        'odoo9-addon-l10n_es_aeat_mod349',
        'odoo9-addon-l10n_es_aeat_sii',
        'odoo9-addon-l10n_es_cnae',
        'odoo9-addon-l10n_es_crm_lead_trade_name',
        'odoo9-addon-l10n_es_dua',
        'odoo9-addon-l10n_es_dua_sii',
        'odoo9-addon-l10n_es_irnr',
        'odoo9-addon-l10n_es_mis_report',
        'odoo9-addon-l10n_es_partner',
        'odoo9-addon-l10n_es_partner_mercantil',
        'odoo9-addon-l10n_es_toponyms',
        'odoo9-addon-payment_redsys',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
