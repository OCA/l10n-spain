# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


def _fill_111_tax_line(env, column, line_xml_id):
    ref = env.ref(line_xml_id)
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO l10n_es_aeat_tax_line
        (res_id, name, field_number, amount, map_line_id, model)
        SELECT t.id, m.name, m.field_number, %s, m.id, '%s'
        FROM %s t
        JOIN l10n_es_aeat_map_tax_line m ON m.id = %s""" % (
            column,
            'l10n.es.aeat.mod111.report',
            'l10n_es_aeat_mod111_report',
            ref.id,
        )
    )


def _fill_111_move_line_refs(env, table, line_xml_id):
    """Fill field move_line_ids."""
    ref = env.ref(line_xml_id)
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO account_move_line_l10n_es_aeat_tax_line_rel
        (l10n_es_aeat_tax_line_id, account_move_line_id)
        SELECT l.id, t.account_move_line
        FROM l10n_es_aeat_tax_line l, %s t
        WHERE l.map_line_id = %%s
        AND l.res_id = t.mod111""" % table, (ref.id, )
    )


def fill_111_values(env):
    """Create tax lines with the data that were previously stored on 111."""
    table_prefix = 'mod111_account_move_line'
    prefix = 'l10n_es_aeat_mod111.aeat_mod111_map_line_'
    _fill_111_tax_line(env, 'casilla_02', prefix + '02')
    _fill_111_tax_line(env, 'casilla_03', prefix + '03')
    _fill_111_tax_line(env, 'casilla_05', prefix + '05')
    _fill_111_tax_line(env, 'casilla_06', prefix + '06')
    _fill_111_tax_line(env, 'casilla_08', prefix + '08')
    _fill_111_tax_line(env, 'casilla_09', prefix + '09')
    _fill_111_move_line_refs(env, table_prefix + '02_rel', prefix + '02')
    _fill_111_move_line_refs(env, table_prefix + '03_rel', prefix + '03')
    _fill_111_move_line_refs(env, table_prefix + '05_rel', prefix + '05')
    _fill_111_move_line_refs(env, table_prefix + '06_rel', prefix + '06')
    _fill_111_move_line_refs(env, table_prefix + '08_rel', prefix + '08')
    _fill_111_move_line_refs(env, table_prefix + '09_rel', prefix + '09')


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    fill_111_values(env)
    # Recompute fields
    records = env['l10n.es.aeat.mod111.report'].search([])
    records._compute_casilla_01()
    records._compute_casilla_04()
    records._compute_casilla_07()
    records._compute_casilla_28()
    records._compute_casilla_30()
