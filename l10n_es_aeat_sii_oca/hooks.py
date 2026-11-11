# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    """Give the SII data of the chart template (registration keys of the fiscal
    positions, Spanish data of some taxes) to the companies that already have
    a Spanish chart of accounts, as the chart template only gives it to the
    records it creates."""
    chart_template = env["account.chart.template"]
    template_data = {
        "account.fiscal.position": (
            chart_template._get_es_common_account_fiscal_position_sii()
        ),
        "account.tax": chart_template._get_es_common_account_tax_sii(),
    }
    for company in env["res.company"].search([]):
        if not (company.chart_template or "").startswith("es_"):
            continue
        for records_data in template_data.values():
            for xml_id, vals in records_data.items():
                record = env.ref(
                    f"account.{company.id}_{xml_id}", raise_if_not_found=False
                )
                if record:
                    record.write(vals)
