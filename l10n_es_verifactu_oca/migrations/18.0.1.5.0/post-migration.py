from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    data = env["account.chart.template"]._parse_csv(
        "es_common_mainland",
        "account.fiscal.position",
        module="l10n_es_verifactu_oca",
    )
    for company in env["res.company"].search([]):
        for xmlid, vals in data.items():
            key_xmlid = vals.get("verifactu_registration_key")
            if not key_xmlid:
                continue
            fp = env.ref(f"account.{company.id}_{xmlid}", raise_if_not_found=False)
            if not fp or fp.verifactu_registration_key:
                continue
            key = env.ref(key_xmlid, raise_if_not_found=False)
            if key:
                fp.verifactu_registration_key = key.id
