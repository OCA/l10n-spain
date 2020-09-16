# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        domain = "['|',('company_id','=',False),('company_id','in',company_ids)]"
        rule = env.ref(
            "l10n_es_vat_book.ir_rule_vat_book_company", raise_if_not_found=False,
        )
        if rule:
            rule.write({"domain_force": domain})
