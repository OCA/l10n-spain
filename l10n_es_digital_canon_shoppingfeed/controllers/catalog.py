from odoo.addons.shoppingfeed_integration.controllers.catalog import CatalogController


class CatalogController(CatalogController):
    _PRODUCT_DATA_FIELDS = [
        *CatalogController._PRODUCT_DATA_FIELDS,
        "l10n_es_digital_canon",
    ]

    _PRODUCT_FETCH_FIELDS = [
        *CatalogController._PRODUCT_FETCH_FIELDS,
        "l10n_es_digital_canon",
    ]

    def _get_product_data(self, store, products):
        product_data = super()._get_product_data(store, products)
        if (
            not store.include_l10n_es_canon_taxes_in_price
            or not store.include_taxes_in_price
        ):
            return product_data
        for data in product_data.values():
            canon_key = data.get("l10n_es_digital_canon")
            if not canon_key:
                continue
            canon_tax = products.env.ref(
                f"account.{store.company_id.id}_tax_template_canon_sale_"
                f"{canon_key.split('.')[0]}",
                raise_if_not_found=False,
            )
            if canon_tax:
                data["taxes_id"] = list(data["taxes_id"]) + [canon_tax.id]
        return product_data
