# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    update_partner_record_detail(cr)
    update_refund_record_detail(cr)


def update_partner_record_detail(cr):
    execute = False
    cr.execute("""SELECT column_name
        FROM information_schema.columns
        WHERE table_name='l10n_es_aeat_mod349_partner_record_detail' AND
        column_name='report_id'""")
    if not cr.fetchone():
        execute = True
        logger.info('Creating field report_id on '
                    'l10n_es_aeat_mod349_partner_record_detail')
        cr.execute(
            """
            ALTER TABLE l10n_es_aeat_mod349_partner_record_detail
            ADD COLUMN report_id integer;
            COMMENT ON COLUMN
            l10n_es_aeat_mod349_partner_record_detail.report_id IS
            'AEAT 349 Report ID';
            """)
    cr.execute("""SELECT column_name
        FROM information_schema.columns
        WHERE table_name='l10n_es_aeat_mod349_partner_record_detail' AND
        column_name='report_type'""")
    if not cr.fetchone():
        execute = True
        logger.info('Creating field report_type on '
                    'l10n_es_aeat_mod349_partner_record_detail')
        cr.execute(
            """ALTER TABLE l10n_es_aeat_mod349_partner_record_detail
            ADD COLUMN report_type VARCHAR"""
        )
    if execute:
        cr.execute("""
            UPDATE l10n_es_aeat_mod349_partner_record_detail
            SET report_id = partner_record.report_id,
                report_type = report.type
            FROM l10n_es_aeat_mod349_partner_record as partner_record
            JOIN l10n_es_aeat_mod349_report as report
            ON report.id = partner_record.report_id
            WHERE partner_record_id = partner_record.id""")


def update_refund_record_detail(cr):
    execute = False
    cr.execute("""SELECT column_name
        FROM information_schema.columns
        WHERE table_name='l10n_es_aeat_mod349_partner_refund_detail' AND
        column_name='report_id'""")
    if not cr.fetchone():
        execute = True
        logger.info('Creating field report_id on '
                    'l10n_es_aeat_mod349_partner_refund_detail')
        cr.execute(
            """
            ALTER TABLE l10n_es_aeat_mod349_partner_refund_detail
            ADD COLUMN report_id integer;
            COMMENT ON COLUMN
            l10n_es_aeat_mod349_partner_refund_detail.report_id IS
            'AEAT 349 Report ID';
            """)
    cr.execute("""SELECT column_name
        FROM information_schema.columns
        WHERE table_name='l10n_es_aeat_mod349_partner_refund_detail' AND
        column_name='report_type'""")
    if not cr.fetchone():
        execute = True
        logger.info('Creating field report_type on '
                    'l10n_es_aeat_mod349_partner_refund_detail')
        cr.execute(
            """ALTER TABLE l10n_es_aeat_mod349_partner_refund_detail
            ADD COLUMN report_type VARCHAR"""
        )
    if execute:
        cr.execute("""
                UPDATE l10n_es_aeat_mod349_partner_refund_detail
                SET report_id = refund_record.report_id,
                    report_type = report.type
                FROM l10n_es_aeat_mod349_partner_refund as refund_record
                JOIN l10n_es_aeat_mod349_report as report
                ON report.id = refund_record.report_id
                WHERE refund_id = refund_record.id""")
