# Copyright 2024 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    cr.execute(
        """
            UPDATE res_partner child
            SET facturae = parent.facturae
            FROM res_partner parent
            WHERE child.facturae != parent.facturae
            AND child.parent_id = parent.id
        """
    )
