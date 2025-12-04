from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Set default use_303 value for existing companies based on their reports."""
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([])

    for company in companies:
        # Get the last report (most recent)
        report = env["l10n.es.aeat.mod390.report"].search(
            [("company_id", "=", company.id)],
            order="id desc",
            limit=1,
        )
        if report:
            company.l10n_es_aeat_mod390_use_303 = report.use_303
