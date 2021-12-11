# Copyright 2020 ForgeFlow <http://www.forgeflow.com>
# Copyright 2021 Tecnativa - João Marques
# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade  # pylint: disable=W7936


def _map_intrastat_product_declaration_month(env):
    _months = [
        (1, "01"),
        (2, "02"),
        (3, "03"),
        (4, "04"),
        (5, "05"),
        (6, "06"),
        (7, "07"),
        (8, "08"),
        (9, "09"),
        (10, "10"),
        (11, "11"),
        (12, "12"),
    ]
    openupgrade.map_values(
        env.cr,
        openupgrade.get_legacy_name("month"),
        "month",
        _months,
        table="l10n_es_intrastat_product_declaration",
    )


def _update_invoice_relation_fields(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE l10n_es_intrastat_product_computation_line ipcl
        SET invoice_line_id = aml.id
        FROM account_invoice_line ail
        JOIN account_move_line aml ON aml.old_invoice_line_id = ail.id
        WHERE ipcl.%(old_line_id)s = ail.id"""
        % {"old_line_id": openupgrade.get_legacy_name("invoice_line_id")},
    )


@openupgrade.migrate()
def migrate(env, version):
    _map_intrastat_product_declaration_month(env)
    _update_invoice_relation_fields(env)
    openupgrade.load_data(
        env.cr, "l10n_es_intrastat_report", "migrations/13.0.1.0.0/noupdate_changes.xml"
    )
