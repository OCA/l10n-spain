import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-l10n-spain",
    description="Meta package for oca-l10n-spain Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-delivery_dhl_parcel',
        'odoo14-addon-delivery_gls_asm',
        'odoo14-addon-delivery_mrw',
        'odoo14-addon-delivery_seur',
        'odoo14-addon-l10n_es_account_asset',
        'odoo14-addon-l10n_es_account_banking_sepa_fsdd',
        'odoo14-addon-l10n_es_account_statement_import_n43',
        'odoo14-addon-l10n_es_aeat',
        'odoo14-addon-l10n_es_aeat_mod111',
        'odoo14-addon-l10n_es_aeat_mod115',
        'odoo14-addon-l10n_es_aeat_mod123',
        'odoo14-addon-l10n_es_aeat_mod130',
        'odoo14-addon-l10n_es_aeat_mod190',
        'odoo14-addon-l10n_es_aeat_mod216',
        'odoo14-addon-l10n_es_aeat_mod303',
        'odoo14-addon-l10n_es_aeat_mod303_oss',
        'odoo14-addon-l10n_es_aeat_mod303_vat_prorate',
        'odoo14-addon-l10n_es_aeat_mod322',
        'odoo14-addon-l10n_es_aeat_mod347',
        'odoo14-addon-l10n_es_aeat_mod349',
        'odoo14-addon-l10n_es_aeat_mod369',
        'odoo14-addon-l10n_es_aeat_mod390',
        'odoo14-addon-l10n_es_aeat_mod390_oss',
        'odoo14-addon-l10n_es_aeat_partner_check',
        'odoo14-addon-l10n_es_aeat_sii_oca',
        'odoo14-addon-l10n_es_aeat_sii_oss',
        'odoo14-addon-l10n_es_aeat_vat_prorrate',
        'odoo14-addon-l10n_es_aeat_vat_prorrate_asset',
        'odoo14-addon-l10n_es_dua',
        'odoo14-addon-l10n_es_dua_sii',
        'odoo14-addon-l10n_es_dua_ticketbai_batuz',
        'odoo14-addon-l10n_es_facturae',
        'odoo14-addon-l10n_es_facturae_efact',
        'odoo14-addon-l10n_es_facturae_face',
        'odoo14-addon-l10n_es_facturae_sale_stock',
        'odoo14-addon-l10n_es_intrastat_report',
        'odoo14-addon-l10n_es_irnr',
        'odoo14-addon-l10n_es_location_nuts',
        'odoo14-addon-l10n_es_mis_report',
        'odoo14-addon-l10n_es_partner',
        'odoo14-addon-l10n_es_partner_mercantil',
        'odoo14-addon-l10n_es_payment_order_confirming_aef',
        'odoo14-addon-l10n_es_payment_order_confirming_sabadell',
        'odoo14-addon-l10n_es_pos',
        'odoo14-addon-l10n_es_pos_by_device',
        'odoo14-addon-l10n_es_reav',
        'odoo14-addon-l10n_es_ticketbai',
        'odoo14-addon-l10n_es_ticketbai_api',
        'odoo14-addon-l10n_es_ticketbai_api_batuz',
        'odoo14-addon-l10n_es_ticketbai_batuz',
        'odoo14-addon-l10n_es_ticketbai_pos',
        'odoo14-addon-l10n_es_toponyms',
        'odoo14-addon-l10n_es_vat_book',
        'odoo14-addon-l10n_es_vat_book_oss',
        'odoo14-addon-l10n_es_vat_prorate',
        'odoo14-addon-payment_redsys',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)