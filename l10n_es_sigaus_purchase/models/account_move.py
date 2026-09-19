# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def sigaus_default_date(self, lines):
        self.ensure_one()
        date = super().sigaus_default_date(lines)
        if not self.invoice_date:
            # Use purchase_order_id if set, else fallback to purchase_line_id.order_id
            purchase_orders = lines.mapped("purchase_order_id") or lines.mapped(
                "purchase_line_id.order_id"
            )
            if purchase_orders:
                date = purchase_orders[0].date_order.date()
        return date

    def _get_sigaus_line_vals(self, lines=False, **kwargs):
        vals = super()._get_sigaus_line_vals(lines, **kwargs)
        purchase_sigaus_line = kwargs.get("purchase_sigaus_line")
        if purchase_sigaus_line:
            vals["purchase_line_id"] = purchase_sigaus_line.id
            vals["purchase_order_id"] = purchase_sigaus_line.order_id.id
        elif lines and lines.mapped("purchase_order_id"):
            vals["purchase_order_id"] = lines.mapped("purchase_order_id")[0].id
        return vals

    @api.model
    def modify_sigaus_line(self, sigaus_line, lines):
        weight = sum(
            line.product_uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
            * line.product_id.weight
            for line in lines
        )
        sigaus_line.quantity = weight

    def manage_purchase_sigaus_lines(self, line_type=None):
        sigaus_lines = self.invoice_line_ids.filtered(
            lambda a: a.is_sigaus and a.purchase_order_id
        )
        for sigaus_line in sigaus_lines:
            order_id = sigaus_line.purchase_order_id
            lines_from_order = self.invoice_line_ids.filtered(
                lambda a, order=order_id: (
                    a.purchase_order_id == order
                    and a.product_id
                    and a.product_id.sigaus_has_amount
                )
            )
            self.modify_sigaus_line(sigaus_line, lines_from_order)

        orders_with_sigaus = (
            self.invoice_line_ids.filtered(lambda a: a.purchase_order_id)
            .mapped("purchase_order_id")
            .filtered(
                lambda o: any(
                    line.product_id.sigaus_has_amount
                    for line in o.order_line.filtered("product_id")
                )
            )
        )

        for order in orders_with_sigaus:
            existing_sigaus_line = sigaus_lines.filtered(
                lambda sl, o=order: sl.purchase_order_id == o
            )
            if not existing_sigaus_line:
                lines = self.invoice_line_ids.filtered(
                    lambda line, o=order: (
                        line.purchase_order_id == o
                        and line.product_id
                        and line.product_id.sigaus_has_amount
                    )
                )
                if lines:
                    purchase_sigaus_line = order.order_line.filtered("is_sigaus")[:1]
                    sigaus_vals = self._get_sigaus_line_vals(
                        lines, purchase_sigaus_line=purchase_sigaus_line
                    )
                    sigaus_vals["purchase_order_id"] = order.id
                    sigaus_vals["purchase_line_id"] = (
                        purchase_sigaus_line.id if purchase_sigaus_line else False
                    )
                    self.env["account.move.line"].create(sigaus_vals)

        sigaus_lines = self.invoice_line_ids.filtered(
            lambda a: a.is_sigaus and a.purchase_order_id
        )
        if len(sigaus_lines) > 1:
            for sigaus_line in sigaus_lines.filtered(
                lambda a: a.purchase_order_id.name not in a.name
            ):
                sigaus_line.name = (
                    f"{sigaus_line.purchase_order_id.name}: {sigaus_line.name}"
                )

    @api.model
    def get_independent_invoice_lines_domain(self):
        domain = super().get_independent_invoice_lines_domain()
        domain += [("purchase_line_id", "=", False)]
        return domain

    def _delete_sigaus(self):
        """Override to avoid deleting SIGAUS lines linked to purchase orders"""
        # Solo eliminar líneas SIGAUS que NO están vinculadas a pedidos de compra
        self.filtered(
            lambda a: a.state in self._sigaus_secondary_unit_fields["editable_states"]
        ).mapped(self._sigaus_secondary_unit_fields["line_ids"]).filtered(
            lambda b: b.is_sigaus and not b.purchase_order_id
        ).unlink()

    def apply_sigaus(self):
        for rec in self.filtered(
            lambda a: a.is_sigaus and a.sigaus_is_date and a.is_purchase_document()
        ):
            rec.manage_purchase_sigaus_lines()
        return super().apply_sigaus()

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        if self.env.context.get("from_purchase"):
            moves.filtered(lambda a: a.is_sigaus).manage_purchase_sigaus_lines()
        return moves

    def copy(self, default=None):
        # 18.0: copy now works on multiple records — keep per-record logic
        copied = self.env["account.move"]
        for rec in self:
            rec_default = dict(default or {})

            # Guardar información de líneas vinculadas a pedidos ANTES de copiar
            purchase_lines_data = []
            if rec.is_sigaus and rec.invoice_line_ids:
                for line in rec.invoice_line_ids.filtered(
                    lambda line: line.purchase_order_id and not line.is_sigaus
                ):
                    purchase_lines_data.append(
                        {
                            "product_id": line.product_id.id,
                            "purchase_order_id": line.purchase_order_id.id,
                            "quantity": line.quantity,
                            "price_unit": line.price_unit,
                        }
                    )

            # Realizar la copia normalmente
            new_move = super(AccountMove, rec).copy(rec_default)

            # Restaurar purchase_order_id en las líneas copiadas y crear líneas
            # SIGAUS
            if purchase_lines_data and new_move.is_sigaus and new_move.sigaus_is_date:
                # Usar contexto para evitar regeneración automática
                new_move = new_move.with_context(avoid_recursion=True)

                # Primero, restaurar purchase_order_id en las líneas de productos
                for data in purchase_lines_data:
                    matching_line = new_move.invoice_line_ids.filtered(
                        lambda line, d=data: (
                            line.product_id.id == d["product_id"]
                            and not line.is_sigaus
                            and abs(line.quantity - d["quantity"]) < 0.01
                            and abs(line.price_unit - d["price_unit"]) < 0.01
                        )
                    )[:1]
                    if matching_line:
                        matching_line.purchase_order_id = data["purchase_order_id"]

                # Ahora buscar líneas con purchase_order_id y productos SIGAUS
                purchase_product_lines = new_move.invoice_line_ids.filtered(
                    lambda line: (
                        line.purchase_order_id
                        and line.product_id
                        and line.product_id.sigaus_has_amount
                    )
                )

                if purchase_product_lines:
                    # Obtener los pedidos únicos
                    orders = purchase_product_lines.mapped("purchase_order_id")

                    # Eliminar TODAS las líneas SIGAUS
                    # (tanto las autogeneradas como las copiadas)
                    # porque vamos a crear nuevas líneas SIGAUS específicas
                    # para cada pedido
                    new_move.invoice_line_ids.filtered(
                        lambda line: line.is_sigaus
                    ).unlink()

                    # Crear línea SIGAUS para cada pedido
                    for order in orders:
                        order_lines = purchase_product_lines.filtered(
                            lambda line, o=order: line.purchase_order_id == o
                        )

                        purchase_sigaus_line = order.order_line.filtered("is_sigaus")[
                            :1
                        ]

                        sigaus_vals = new_move._get_sigaus_line_vals(
                            order_lines, purchase_sigaus_line=purchase_sigaus_line
                        )
                        sigaus_vals["move_id"] = new_move.id
                        self.env["account.move.line"].create(sigaus_vals)

                # Restaurar el contexto
                new_move = new_move.with_context(avoid_recursion=False)

            copied |= new_move
        return copied
