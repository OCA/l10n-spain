# Copyright 2023 Studio73 - Roger Amorós
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

from odoo.tools.sql import column_exists, create_column

intr_prod_dec_fields = [
    "message_main_attachment_id",
    "company_id",
    "company_country_code",
    "state",
    "note",
    "year",
    "month",
    "year_month",
    "declaration_type",
    "action",
    "revision",
    "num_decl_lines",
    "total_amount",
    "reporting_level",
    "xml_attachment_id",
]
intr_prod_comp_lin_fields = [
    "invoice_line_id",
    "src_dest_country_id",
    "src_dest_country_code",
    "hs_code_id",
    "weight",
    "suppl_unit_qty",
    "amount_company_currency",
    "amount_accessory_cost_company_currency",
    "transaction_id",
    "region_id",
    "product_origin_country_id",
    "product_origin_country_code",
    "vat",
    "partner_vat",
    "incoterm_id",
    "transport_id",
    "intrastat_state_id",
]
intr_prod_dec_lin_fields = [
    "src_dest_country_id",
    "src_dest_country_code",
    "hs_code_id",
    "suppl_unit_qty",
    "transaction_id",
    "region_id",
    "product_origin_country_id",
    "product_origin_country_code",
    "vat",
    "incoterm_id",
    "transport_id",
    "intrastat_state_id",
    "weight",
    "amount_company_currency",
    "partner_vat",
]


@openupgrade.migrate()
def migrate(env, version):
    if not column_exists(env.cr, "intrastat_product_declaration", "old_l10n_es_id"):
        create_column(
            env.cr, "intrastat_product_declaration", "old_l10n_es_id", "numeric"
        )
    if not column_exists(
        env.cr, "intrastat_product_declaration_line", "old_l10n_es_id"
    ):
        create_column(
            env.cr, "intrastat_product_declaration_line", "old_l10n_es_id", "numeric"
        )
    if not column_exists(
        env.cr, "intrastat_product_computation_line", "old_l10n_es_id"
    ):
        create_column(
            env.cr, "intrastat_product_computation_line", "old_l10n_es_id", "numeric"
        )
    new_fields = ", ".join(f'"{f}"' for f in ["old_l10n_es_id"] + intr_prod_dec_fields)
    old_fields = ", ".join(f'"{f}"' for f in ["id"] + intr_prod_dec_fields)
    query = """INSERT INTO intrastat_product_declaration ({new_fields})
        SELECT {old_fields} FROM l10n_es_intrastat_product_declaration
    """.format(
        new_fields=new_fields, old_fields=old_fields
    )
    openupgrade.logged_query(env.cr, query)

    new_fields = ", ".join(
        f"{f}" for f in ["old_l10n_es_id"] + intr_prod_dec_lin_fields
    )
    old_fields = ", ".join(f"leipd.{f}" for f in ["id"] + intr_prod_dec_lin_fields)
    query = """INSERT INTO intrastat_product_declaration_line (parent_id, {new_fields})
        SELECT ipd.id, {old_fields}
        FROM l10n_es_intrastat_product_declaration_line AS leipd
        INNER JOIN intrastat_product_declaration
        AS ipd ON ipd.old_l10n_es_id = leipd.parent_id
    """.format(
        new_fields=new_fields, old_fields=old_fields
    )
    openupgrade.logged_query(env.cr, query)

    new_fields = ", ".join(
        f"{f}" for f in ["old_l10n_es_id"] + intr_prod_comp_lin_fields
    )
    old_fields = ", ".join(f"leipc.{f}" for f in ["id"] + intr_prod_comp_lin_fields)
    query = """INSERT INTO intrastat_product_computation_line
            (parent_id, declaration_line_id, {new_fields})
        SELECT ipd.id, leipd.id, {old_fields}
        FROM l10n_es_intrastat_product_computation_line AS leipc
        INNER JOIN intrastat_product_declaration
        AS ipd ON ipd.old_l10n_es_id = leipc.parent_id
        INNER JOIN intrastat_product_declaration_line
        AS leipd ON leipd.old_l10n_es_id = leipc.declaration_line_id
    """.format(
        new_fields=new_fields, old_fields=old_fields
    )
    openupgrade.logged_query(env.cr, query)
