# -*- coding: utf-8 -*-
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

# Rename field: origin_invoices_ids -> origin_invoice_ids
# Rename field: refund_invoices_description -> refund_reason
column_renames = {
    'account_invoice': [
        ('origin_invoices_ids', 'origin_invoice_ids'),
        ('refund_invoices_description', 'refund_reason'),
    ],
}


def migrate(cr, version):
    openupgrade.rename_columns(cr, column_renames)
