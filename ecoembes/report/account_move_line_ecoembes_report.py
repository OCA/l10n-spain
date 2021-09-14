# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools


class AccountMoveLineEcoembesReport(models.Model):
    _name = "account.move.line.ecoembes.report"
    _description = "Account Move Lines Ecoembes report"
    _auto = False

    period = fields.Char(string="Period", readonly=True)
    product_id = fields.Many2one(
        comodel_name="product.product", string="Product", readonly=True
    )
    product_name = fields.Char(
        related="product_id.name", string="Product name", readonly=True
    )
    default_code = fields.Char(
        related="product_id.default_code", readonly=True, store=True
    )
    quantity = fields.Float(string="Quantity", readonly=True)
    billing = fields.Float(string="Billing", readonly=True)
    move_id = fields.Many2one(comodel_name="account.move", string="Move", readonly=True)
    invoice_date = fields.Date(
        related="move_id.invoice_date", readonly=True, string="Invoice Date"
    )

    @api.model
    def _select(self):
        return """
            SELECT
                line.id,
                EXTRACT(YEAR FROM move.invoice_date) AS "period",
                line.product_id,
                pp.default_code,
                sum(
                    CASE
                        WHEN move.type='out_refund'
                    THEN (- line.quantity) / u.factor * u2.factor
                        ELSE line.quantity / u.factor * u2.factor
                    END
                ) AS "quantity",
                sum(
                    CASE
                        WHEN move.type = 'out_refund'  THEN - line.price_subtotal
                        ELSE line.price_subtotal
                    END
                ) AS "billing",
                line.move_id
        """

    @api.model
    def _from(self):
        return """
            FROM account_move_line line
                INNER JOIN account_move move ON line.move_id = move.id
                INNER JOIN res_partner partner ON move.partner_id = partner.id
                INNER JOIN res_country country on partner.country_id = country.id
                INNER JOIN product_product pp ON line.product_id = pp.id
                INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
                LEFT JOIN uom_uom u ON u.id = line.product_uom_id
                LEFT JOIN uom_uom u2 ON u2.id = pt.uom_id
        """

    @api.model
    def _where(self):
        return """
            WHERE move.state NOT IN ('cancel', 'draft')
                AND pp.ecoembes_sig IS true
                AND pt.type != 'service'
                AND move.type IN ('out_invoice','out_refund')
                AND country.code = 'ES'
        """

    @api.model
    def _group_by(self):
        return """
            GROUP BY
                line.id,
                line.product_id,
                pp.default_code,
                EXTRACT(YEAR FROM move.invoice_date),
                line.move_id
        """

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        # pylint: disable=sql-injection
        self.env.cr.execute(
            """
            CREATE OR REPLACE VIEW %s AS (
                %s %s %s %s
            )
        """
            % (
                self._table,
                self._select(),
                self._from(),
                self._where(),
                self._group_by(),
            )
        )
