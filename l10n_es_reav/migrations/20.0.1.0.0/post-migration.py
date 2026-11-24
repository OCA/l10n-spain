# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from openupgradelib import openupgrade

from odoo.addons.l10n_es_reav.models.account_chart_template import REAV_KEPT_TAXES

_logger = logging.getLogger(__name__)

# Taxes of the Odoo core chart that the REAV taxes replace since 20.0.1.0.0 and
# not in 18.0, by the xmlid of the REAV tax
REAV_NEW_ORIGINAL_TAXES = {
    "account_tax_template_p_reav0": (
        "account_tax_template_p_iva0_s_bc",
        "account_tax_template_p_iva0_s_sc",
        "account_tax_template_p_iva2_bc",
        "account_tax_template_p_iva2_sc",
        "account_tax_template_p_iva5_bc",
        "account_tax_template_p_iva5_sc",
        "account_tax_template_p_iva7-5_bc",
        "account_tax_template_p_iva7-5_sc",
        "account_tax_template_p_iva0_nd",
        "account_tax_template_p_iva10_nd",
        "account_tax_template_p_iva4_nd",
        "account_tax_template_p_iva2_nd",
        "account_tax_template_p_iva5_nd",
        "account_tax_template_p_iva7-5_nd",
    ),
    "account_tax_template_s_reav0": (
        "account_tax_template_s_iva0b",
        "account_tax_template_s_iva0s",
        "account_tax_template_s_iva2b",
        "account_tax_template_s_iva2s",
        "account_tax_template_s_iva5b",
        "account_tax_template_s_iva5s",
        "account_tax_template_s_iva7-5b",
        "account_tax_template_s_iva7-5s",
    ),
}


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
    # The purchase tax of the REAV is not deductible (art. 146 LIVA): the SII
    # sends it as such (key 05, deductible quota 0). Only the default type of
    # the field is replaced, not one chosen by the user.
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_tax tax
           SET l10n_es_type = 'no_deducible'
          FROM ir_model_data imd
         WHERE imd.module = 'account' AND imd.model = 'account.tax'
           AND imd.res_id = tax.id
           AND SUBSTRING(imd.name FROM '^[0-9]+_(.*)$') = 'account_tax_template_p_reav0'
           AND COALESCE(tax.l10n_es_type, 'sujeto') = 'sujeto'
        """,
    )
    _link_kept_taxes(env)
    _link_new_original_taxes(env)
    _warn_products_with_reav_taxes(env)


def _link_kept_taxes(env):
    """The REAV fiscal position keeps the taxes outside the special regime, as
    the chart template does: in 18.0 a tax that a fiscal position didn't map
    stayed on the invoice, since 19.0 it is removed unless the position is one
    of the fiscal positions of the tax."""
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO account_fiscal_position_account_tax_rel
            (account_fiscal_position_id, account_tax_id)
        SELECT fp_imd.res_id, tax_imd.res_id
          FROM ir_model_data fp_imd
          JOIN ir_model_data tax_imd
            ON tax_imd.module = 'account' AND tax_imd.model = 'account.tax'
           AND SUBSTRING(tax_imd.name FROM '^([0-9]+)_')
               = SUBSTRING(fp_imd.name FROM '^([0-9]+)_')
           AND SUBSTRING(tax_imd.name FROM '^[0-9]+_(.*)$') IN %s
         WHERE fp_imd.module = 'account'
           AND fp_imd.model = 'account.fiscal.position'
           AND SUBSTRING(fp_imd.name FROM '^[0-9]+_(.*)$') = 'fp_reav'
        ON CONFLICT DO NOTHING
        """,
        [REAV_KEPT_TAXES],
    )


def _link_new_original_taxes(env):
    """The REAV taxes replace the VAT of every rate, as the chart template does.
    OpenUpgrade only converts the replacements of 18.0 and a chart reload only
    adds replacements towards new taxes, so without them the REAV position
    removes those taxes from the invoices since 19.0 (`map_tax`)."""
    pairs = [
        (dest, src)
        for dest, sources in REAV_NEW_ORIGINAL_TAXES.items()
        for src in sources
    ]
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO account_tax_alternatives (dest_tax_id, src_tax_id)
        SELECT dest_tax.id, src_tax.id
          FROM unnest(%s::varchar[], %s::varchar[]) AS pair(dest, src)
          JOIN ir_model_data dest_imd
            ON dest_imd.module = 'account' AND dest_imd.model = 'account.tax'
           AND SUBSTRING(dest_imd.name FROM '^[0-9]+_(.*)$') = pair.dest
          JOIN account_tax dest_tax ON dest_tax.id = dest_imd.res_id
          JOIN ir_model_data src_imd
            ON src_imd.module = 'account' AND src_imd.model = 'account.tax'
           AND SUBSTRING(src_imd.name FROM '^([0-9]+)_')
               = SUBSTRING(dest_imd.name FROM '^([0-9]+)_')
           AND SUBSTRING(src_imd.name FROM '^[0-9]+_(.*)$') = pair.src
          JOIN account_tax src_tax ON src_tax.id = src_imd.res_id
        ON CONFLICT DO NOTHING
        """,
        [[dest for dest, _src in pairs], [src for _dest, src in pairs]],
    )


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
