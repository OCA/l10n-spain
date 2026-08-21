# Copyright 2026 - OCA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

ATC_VERIFACTU_TAX_KEY = "03"


def post_init_hook(env):
    """Initialize VERI*FACTU IGIC keys for pending drafts and fiscal positions.

    Only draft customer documents and fiscal positions are updated. Posted or
    historical invoices are left unchanged (outside VERI*FACTU scope).
    """
    atc_agency = env.ref(
        "l10n_es_aeat.aeat_tax_agency_canarias", raise_if_not_found=False
    )
    if not atc_agency:
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
    if fiscal_positions:
        fiscal_positions.write({"verifactu_tax_key": ATC_VERIFACTU_TAX_KEY})

    draft_moves = env["account.move"].search(
        [
            ("company_id", "in", companies.ids),
            ("state", "=", "draft"),
            ("move_type", "in", ("out_invoice", "out_refund")),
        ]
    )
    if draft_moves:
        draft_moves._compute_verifactu_tax_key()
        draft_moves._compute_verifactu_registration_key()
