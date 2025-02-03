# Copyright 2024 Aritz Olea <aritz.olea@factorlibre.com>
# Copyright 2025 Luis Rodríguez <luis.rodriguez@dixmit.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade

taxes_to_rename = [
    (
        "l10n_es_irnr.%s_account_tax_template_s_irpfnrnue24",
        "l10n_es.%s_account_tax_template_s_irpfnrnue24",
    ),
    (
        "l10n_es_irnr.%s_account_tax_template_p_irpfnrnue24p",
        "l10n_es.%s_account_tax_template_p_irpfnrnue24p",
    ),
    (
        "l10n_es_irnr.%s_account_tax_template_s_irpfnrue19",
        "l10n_es.%s_account_tax_template_s_irpfnrue19",
    ),
    (
        "l10n_es_irnr.%s_account_tax_template_p_irpfnrue19p",
        "l10n_es.%s_account_tax_template_p_irpfnrue19p",
    ),
    (
        "l10n_es_irnr.%s_account_tax_template_s_irpfnrnue0",
        "l10n_es.%s_account_tax_template_s_irpfnrnue0",
    ),
    (
        "l10n_es_irnr.%s_account_tax_template_p_irpfnrnue0p",
        "l10n_es.%s_account_tax_template_p_irpfnrnue0p",
    ),
    (
        "l10n_es_irnr.%s_account_tax_template_s_irpfnrue0",
        "l10n_es.%s_account_tax_template_s_irpfnrue0",
    ),
    (
        "l10n_es_irnr.%s_account_tax_template_p_irpfnrue0p",
        "l10n_es.%s_account_tax_template_p_irpfnrue0p",
    ),
]


def rename_xmlids(env):
    for company in env["res.company"].search([]):
        taxes_to_rename_by_company = [
            (a % company.id, b % company.id) for (a, b) in taxes_to_rename
        ]
        openupgrade.rename_xmlids(env.cr, taxes_to_rename_by_company)


def migrate_tax_groups(env):
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


@openupgrade.migrate()
def migrate(env, version):

    migrate_tax_groups(env)
    rename_xmlids(env)
