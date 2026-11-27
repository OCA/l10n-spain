# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import tools

ATC_VERIFACTU_CANARY_TAX_KEY = "03"

# xmlid suffix (account.{company_id}_*) → VERI*FACTU IGIC registration key
CANARY_FP_REGISTRATION_KEYS = {
    "fp_canary_1": "verifactu_registration_keys_igic_01",
    "fp_nacional_canary_ns": "verifactu_registration_keys_igic_08",
    "fp_extra_canary": "verifactu_registration_keys_igic_02",
    "fp_recargo_canary": "verifactu_registration_keys_igic_01",
    "fp_irpf9_canary": "verifactu_registration_keys_igic_01",
    "fp_irpf15_canary": "verifactu_registration_keys_igic_01",
    "fp_irpf19a_canary": "verifactu_registration_keys_igic_01",
    "fp_ispn_canary": "verifactu_registration_keys_igic_01",
    "fp_retailer_canary": "verifactu_registration_keys_igic_17",
    "fp_dua": "verifactu_registration_keys_igic_01",
}


def pre_init_hook(env):
    """Avoid the heavy compute methods, specially when account.move table is very
    populated, pre-creating the columns and filling them with sane defaultes. Some of it
    is done on post-init hook.
    WARNING: For special cases like IGIC or other, the default value doesn't serve.
    """
    cr = env.cr
    column_exists = tools.sql.column_exists
    create_column = tools.sql.create_column
    if not column_exists(cr, "account_move", "verifactu_refund_type"):
        create_column(cr, "account_move", "verifactu_refund_type", "varchar")
        cr.execute(
            "UPDATE account_move SET verifactu_refund_type = 'I' "
            "WHERE move_type = 'out_refund'"
        )
    if not column_exists(cr, "account_move", "verifactu_registration_key"):
        create_column(cr, "account_move", "verifactu_registration_key", "int4")
        # Initialization done on post-init
    if not column_exists(cr, "account_move", "verifactu_tax_key"):
        create_column(cr, "account_move", "verifactu_tax_key", "varchar")
        cr.execute(
            "UPDATE account_move SET verifactu_tax_key = '01' "
            "WHERE move_type IN ('out_invoice', 'out_refund') "
            "AND state = 'draft'"
        )
    _backfill_canary_verifactu_keys(env)


def _assign_canary_fp_registration_keys(env, companies):
    """Fill registration keys on native Canary fiscal positions already loaded."""
    imd = env["ir.model.data"].sudo()
    for company in companies:
        for suffix, key_xmlid in CANARY_FP_REGISTRATION_KEYS.items():
            fp_data = imd.search(
                [
                    ("module", "=", "account"),
                    ("model", "=", "account.fiscal.position"),
                    ("name", "=", f"{company.id}_{suffix}"),
                ],
                limit=1,
            )
            if not fp_data:
                continue
            fp = env["account.fiscal.position"].browse(fp_data.res_id)
            if fp.verifactu_registration_key:
                continue
            key = env.ref(f"l10n_es_verifactu_oca.{key_xmlid}")
            fp.verifactu_registration_key = key


def _backfill_canary_verifactu_keys(env):
    """Assign IGIC keys to existing Canary fiscal positions and draft documents."""
    atc_agency = env.ref(
        "l10n_es_aeat.aeat_tax_agency_canarias", raise_if_not_found=False
    )
    default_key = env.ref(
        "l10n_es_verifactu_oca.verifactu_registration_keys_igic_01",
        raise_if_not_found=False,
    )
    if not atc_agency or not default_key:
        return
    companies = env["res.company"].search([("tax_agency_id", "=", atc_agency.id)])
    if not companies:
        return

    fiscal_positions = env["account.fiscal.position"].search(
        [
            ("company_id", "in", companies.ids),
            "|",
            ("verifactu_tax_key", "=", False),
            ("verifactu_tax_key", "=", "01"),
        ]
    )
    fiscal_positions.verifactu_tax_key = ATC_VERIFACTU_CANARY_TAX_KEY
    _assign_canary_fp_registration_keys(env, companies)

    draft_moves = env["account.move"].search(
        [
            ("company_id", "in", companies.ids),
            ("state", "=", "draft"),
            ("move_type", "in", ("out_invoice", "out_refund")),
        ]
    )
    for fiscal_position, moves in draft_moves.grouped("fiscal_position_id").items():
        moves.verifactu_tax_key = (
            fiscal_position.verifactu_tax_key
            if fiscal_position
            else ATC_VERIFACTU_CANARY_TAX_KEY
        )
        moves.verifactu_registration_key = (
            fiscal_position.verifactu_registration_key
            if fiscal_position and fiscal_position.verifactu_registration_key
            else default_key
        )


def post_init_hook(env):
    """Initialize VERI*FACTU keys after the registration keys have been loaded."""
    key = env.ref("l10n_es_verifactu_oca.verifactu_registration_keys_01")
    env.cr.execute(
        "UPDATE account_move SET verifactu_registration_key = %s "
        "WHERE move_type IN ('out_invoice', 'out_refund') "
        "AND state = 'draft' "
        "AND verifactu_registration_key IS NULL",
        (key.id,),
    )
    _backfill_canary_verifactu_keys(env)
