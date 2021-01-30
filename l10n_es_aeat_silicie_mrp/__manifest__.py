{
    "name": "SILICIE MRP",
    "version": "12.0.1.0.0",
    "category": "Accounting & Finance",
    "author": "Alquemy,"
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "l10n_es_aeat_silicie",
        "mrp",
    ],
    "data": [
        "wizards/silicie_move_editor_views.xml",
        "views/mrp_production_views.xml",
        "views/mrp_routing_views.xml",
        "views/product_views.xml",
        "views/stock_production_lot_views.xml",
        "views/stock_scrap_views.xml",
    ],
}
