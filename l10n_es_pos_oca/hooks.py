# Copyright 2018 David Vidal <david.vidal@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry, vals=None):
    """For brand new installations"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    IrSequence = env["ir.sequence"]
    pos_config = env["pos.config"].search(
        [("l10n_es_simplified_invoice_sequence_id", "=", False)]
    )
    pos_name_dupes = {}
    vals = {} if vals is None else vals
    for pos in pos_config:
        pos_name_dupes.setdefault(pos.name, -1)
        pos_name_dupes[pos.name] += 1
        pos_vals = vals.get(pos, {})
        pos_name = (
            pos.name
            if not pos_name_dupes[pos.name]
            else "%s_%d" % (pos.name, pos_name_dupes[pos.name])
        )
        if not pos_vals.get("prefix"):
            pos_vals["prefix"] = initial_prefix = "{}{}".format(
                pos_name, pos._get_default_prefix()
            )
            ith = 0
            while IrSequence.search_count([("prefix", "=", pos_vals["prefix"])]):
                ith += 1
                pos_vals["prefix"] = "{}_{}".format(initial_prefix, ith)
        pos.l10n_es_simplified_invoice_sequence_id = IrSequence.create(
            {
                "name": (
                    pos.with_context(lang=env.user.lang)._get_l10n_es_sequence_name()
                    % pos_name
                ),
                "prefix": pos_vals.get(
                    "prefix", "{}{}".format(pos_name, pos._get_default_prefix())
                ),
                "padding": pos_vals.get("padding", pos._get_default_padding()),
                "implementation": pos_vals.get("implementation", "standard"),
                "code": "pos.config.simplified_invoice",
                "company_id": pos_vals.get("company_id", pos.company_id.id),
            }
        )


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["ir.sequence"].search([("code", "=", "pos.config.simplified_invoice")]).unlink()
