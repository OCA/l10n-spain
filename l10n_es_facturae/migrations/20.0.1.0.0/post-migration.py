# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import csv

from openupgradelib import openupgrade

from odoo.tools import file_open


@openupgrade.migrate()
def migrate(env, version):
    """The taxes of the Spanish chart that had no Facturae code get the one of
    the chart template, without changing the codes already set."""
    companies = env["res.company"].search([("chart_template", "=like", "es_%")])
    with file_open(
        "l10n_es_facturae/data/template/account.tax-es_common.csv"
    ) as template_file:
        for record in csv.DictReader(template_file):
            for company in companies:
                tax = env.ref(
                    f"account.{company.id}_{record['id']}", raise_if_not_found=False
                )
                if tax and not tax.facturae_code:
                    tax.facturae_code = record["facturae_code"]
