# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


def fill_dates(env):
    """Fill start/end dates, based on the periods
    that were being used in 8.0"""

    q_subquery = """
        SELECT abr.id, min(ap.date_start) AS min_date_start,
               max(ap.date_stop) AS max_date_stop
        FROM %s AS rel
        JOIN account_balance_reporting AS abr
        ON abr.id = rel.account_balance_reporting_id
        JOIN account_period AS ap
        ON ap.id = rel.period_id
        WHERE abr.check_filter = 'periods'
        GROUP BY abr.id
    """

    q_subquery_actual = q_subquery % \
        'account_balance_reporting_account_period_current_rel'

    # Migrar periodos actuales
    query_periodos_actuales = """
        UPDATE account_balance_reporting as abr
        SET current_date_from = Q.min_date_start,
            current_date_to = Q.max_date_stop
        FROM (%s) AS Q
        where abr.id = Q.id
    """ % q_subquery_actual

    openupgrade.logged_query(env.cr, query_periodos_actuales)

    # Migrar ejercicio fiscal actual, si no hay periodos
    query_ejercicio_actual = """
        UPDATE account_balance_reporting as abr
        SET current_date_from = fy.date_start,
            current_date_to = fy.date_stop
        FROM account_balance_reporting as abr2
        INNER JOIN account_fiscalyear AS fy
        ON fy.id = abr2.current_fiscalyear_id
        LEFT JOIN account_balance_reporting_account_period_current_rel AS rel
        ON abr2.id = rel.account_balance_reporting_id
        WHERE rel.period_id IS NULL
        AND abr2.check_filter = 'periods'
        AND abr2.id = abr.id
    """

    openupgrade.logged_query(env.cr, query_ejercicio_actual)

    q_subquery_anterior = q_subquery % \
        'account_balance_reporting_account_period_previous_rel'

    # Migrar periodos anteriores
    query_periodos_anteriores = """
        UPDATE account_balance_reporting as abr
        SET previous_date_from = Q.min_date_start,
            previous_date_to = Q.max_date_stop
        FROM (%s) as Q
        where abr.id = Q.id
    """ % q_subquery_anterior

    openupgrade.logged_query(env.cr, query_periodos_anteriores)

    # Migrar ejercicio fiscal anterior, si no hay periodos
    query_ejercicio_anterior = """
        UPDATE account_balance_reporting as abr
        SET previous_date_from = fy.date_start,
            previous_date_to = fy.date_stop
        FROM account_balance_reporting as abr2
        INNER JOIN account_fiscalyear AS fy
        ON fy.id = abr2.previous_fiscalyear_id
        LEFT JOIN account_balance_reporting_account_period_previous_rel AS rel
        ON abr2.id = rel.account_balance_reporting_id
        WHERE rel.period_id IS NULL
        AND abr2.check_filter = 'periods'
        AND abr2.id = abr.id
    """

    openupgrade.logged_query(env.cr, query_ejercicio_anterior)


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return
    fill_dates(env)
