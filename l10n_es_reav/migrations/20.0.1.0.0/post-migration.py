# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """The REAV taxes get the travel agencies regime code (key 05 of the SII and
    VERI*FACTU) and the VAT applicability of the chart template, which a chart
    reload does not write on existing taxes."""
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_tax tax
           SET l10n_es_regime_code = COALESCE(tax.l10n_es_regime_code, '05'),
               l10n_es_applicability = COALESCE(tax.l10n_es_applicability, '01')
          FROM ir_model_data imd
         WHERE imd.module = 'account' AND imd.model = 'account.tax'
           AND imd.res_id = tax.id
           AND SUBSTRING(imd.name FROM '^[0-9]+_(.*)$') IN (
               'account_tax_template_p_reav0', 'account_tax_template_s_reav0'
           )
        """,
    )
    _warn_products_with_reav_taxes(env)


def _warn_products_with_reav_taxes(env):
    """Since 19.0 the REAV taxes are applied only by the REAV fiscal position,
    and they are removed from the invoices with the domestic one: the products
    that had them as their taxes (the usage of 18.0) must get the general VAT
    taxes, and their customers and suppliers the REAV fiscal position."""
    env.cr.execute(
        """
        SELECT res_id FROM ir_model_data
         WHERE module = 'account' AND model = 'account.tax'
           AND SUBSTRING(name FROM '^[0-9]+_(.*)$') IN (
               'account_tax_template_p_reav0', 'account_tax_template_s_reav0'
           )
        """
    )
    tax_ids = [row[0] for row in env.cr.fetchall()]
    products = (
        env["product.template"]
        .with_context(active_test=False)
        .search(
            ["|", ("taxes_id", "in", tax_ids), ("supplier_taxes_id", "in", tax_ids)]
        )
    )
    if products:
        _logger.warning(
            "These products have REAV taxes, which are now removed from the "
            "invoices without the REAV fiscal position: set the general VAT taxes "
            "on them and the REAV fiscal position on the travel agencies contacts: "
            "%s",
            ", ".join(products.mapped("display_name")),
        )
