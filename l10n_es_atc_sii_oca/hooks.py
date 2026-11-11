# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .models.account_chart_template import igic_tax_data


def post_init_hook(env):
    """Give the Spanish data of the IGIC taxes to the companies that already
    have a Spanish chart of accounts, as the chart template only gives it to
    the taxes it creates. Nothing has been sent to the SII of the Canary tax
    agency with them yet, so the used taxes get it too."""
    for company in env["res.company"].search([]):
        if not (company.chart_template or "").startswith("es_"):
            continue
        for xml_id, vals in igic_tax_data().items():
            tax = env.ref(f"account.{company.id}_{xml_id}", raise_if_not_found=False)
            if tax:
                tax.write(vals)
