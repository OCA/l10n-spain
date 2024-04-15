import csv

from odoo.tools import file_open


def post_init_hook(env):
    """We need to replace the existing spanish taxes with the new field values"""
    companies = env.companies.filtered(
        lambda company: company.chart_template
        and company.chart_template.startswith("es_")
    )
    current_taxes = env["account.tax"].search(
        env["account.tax"]._check_company_domain(companies)
    )
    tax_map = {tax: tax_id for tax_id, tax in current_taxes.get_external_id().items()}

    with file_open(
        "l10n_es_facturae/data/template/account.tax-es_common.csv"
    ) as template_file:
        for record in csv.DictReader(template_file):
            for company in companies:
                tax_id = tax_map.get("account.{}_{}".format(company.id, record["id"]))
                if tax_id:
                    env["account.tax"].browse(tax_id).write(
                        {"facturae_code": record["facturae_code"]}
                    )
