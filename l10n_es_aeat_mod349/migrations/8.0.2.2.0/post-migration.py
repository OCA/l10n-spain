# -*- coding: utf-8 -*-
# © 2017 Punt Sistemes, S.L.U.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):

    cr.execute(
        """
        UPDATE account_account
        SET not_in_mod349 = True
        WHERE code like '407%' OR code like '438%';
        """)
