# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


def fill_dates(env):
    """Fill start/end dates, based on the periods that used to be in 8.0."""
    for field in ('current', 'previous'):
        q_subquery = """
            SELECT abr.id, min(ap.date_start) AS min_date_start,
                   max(ap.date_stop) AS max_date_stop
            FROM account_balance_reporting_account_period_%s_rel AS rel
            JOIN account_balance_reporting AS abr
            ON abr.id = rel.account_balance_reporting_id
            JOIN account_period AS ap
            ON ap.id = rel.period_id
            WHERE abr.check_filter = 'periods'
            GROUP BY abr.id
        """ % field
        # Migrate when periods are specified
        query_periods = """
            UPDATE account_balance_reporting as abr
            SET %s_date_from = Q.min_date_start,
                %s_date_to = Q.max_date_stop
            FROM (%s) AS Q
            where abr.id = Q.id
        """ % (field, field, q_subquery)
        openupgrade.logged_query(env.cr, query_periods)
        # Migrate full fiscal year if no periods
        query_no_periods = """
            UPDATE account_balance_reporting as abr
            SET %s_date_from = fy.date_start,
                %s_date_to = fy.date_stop
            FROM account_balance_reporting as abr2
            INNER JOIN account_fiscalyear AS fy
            ON fy.id = abr2.%s_fiscalyear_id
            LEFT JOIN account_balance_reporting_account_period_%s_rel AS rel
            ON abr2.id = rel.account_balance_reporting_id
            WHERE rel.period_id IS NULL
            AND abr2.check_filter = 'periods'
            AND abr2.id = abr.id
        """ % (field, field, field, field)
        openupgrade.logged_query(env.cr, query_no_periods)


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    fill_dates(env)
