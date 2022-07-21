# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class MRWWarehouseDepartmentMap(models.Model):
    _name = "mrw.department.wh.map"

    warehouse_id = fields.Many2one(comodel_name="stock.warehouse", required=True)
    department_number = fields.Char(required=True)

    _sql_constraints = [
        (
            "wh_uniq",
            "unique (warehouse_id)",
            "A Warehouse can only have one department associated!",
        )
    ]
