# Copyright 2024 Aritz Olea <aritz.olea@factorlibre.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    retenciones_24 = env.ref("l10n_es.tax_group_retenciones_24")
    retenciones_19 = env.ref("l10n_es.tax_group_retenciones_19")
    retenciones_0 = env.ref("l10n_es.tax_group_retenciones_0")
    tax_write_list = [
        ("account_tax_template_s_irpfnrnue24", retenciones_24),
        ("account_tax_template_p_irpfnrnue24p", retenciones_24),
        ("account_tax_template_s_irpfnrue19", retenciones_19),
        ("account_tax_template_p_irpfnrue19p", retenciones_19),
        ("account_tax_template_s_irpfnrnue0", retenciones_0),
        ("account_tax_template_p_irpfnrnue0p", retenciones_0),
        ("account_tax_template_s_irpfnrue0", retenciones_0),
        ("account_tax_template_p_irpfnrue0p", retenciones_0),
    ]
    for tax_write in tax_write_list:
        record_ids = (
            env["ir.model.data"]
            .search(
                [
                    ("model", "=", "account.tax"),
                    ("name", "like", tax_write[0]),
                ]
            )
            .mapped("res_id")
        )
        env["account.tax"].browse(record_ids).tax_group_id = tax_write[1]
