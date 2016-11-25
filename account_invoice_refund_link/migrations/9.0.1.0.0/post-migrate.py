# -*- coding: utf-8 -*-
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.account_invoice_refund_link.hooks import post_init_hook


def migrate(cr, version):
    # Link all refund invoices to its original invoices
    post_init_hook(cr, None)
