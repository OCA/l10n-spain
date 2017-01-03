# -*- coding: utf-8 -*-
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3).


def migrate(cr, version):
    """Fill comercial field on childs. It doesn't work for more than 2 level
    partners."""
    if not version:
        return
    cr.execute("""
        UPDATE res_partner rp
        SET comercial = parent.comercial
        FROM res_partner parent
        WHERE parent.id = rp.parent_id
        AND rp.comercial IS NULL
        AND parent.comercial IS NOT NULL
        """)
