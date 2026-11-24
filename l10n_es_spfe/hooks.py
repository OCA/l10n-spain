# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    """Auto-configure UNECE and SPFE attributes on Spanish company taxes & journals."""
    spanish_companies = env["res.company"].search(
        [("partner_id.country_id.code", "=", "ES")]
    )
    if spanish_companies:
        env["account.journal"].search(
            [
                ("company_id", "in", spanish_companies.ids),
                ("type", "in", ("sale", "purchase")),
            ]
        ).spfe_enabled = True
        spanish_companies._configure_spfe_spanish_taxes()
