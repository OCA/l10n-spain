from odoo import _, exceptions, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _set_chaining_invoice(self):
        """PoS Config has a different chain for VERI*FACTU"""
        if self.pos_order_ids and len(self.pos_order_ids.ids) == 1:
            # TODO: use cases
            # * The Invoice is created from the PoS
            # * The Invoice is created later after some time, in this case
            #   the PoS order (simplified invoice) is already in the chain
            pos_order = self.pos_order_ids
            if not pos_order.verifactu_previous_invoice_id:
                return pos_order._set_chaining_invoice()
        elif len(self.pos_order_ids) > 1:
            # TODO: is possible to have multiple PoS orders for the same Invoice?
            raise exceptions.UserError(
                _("VERI*FACTU: multiple PoS Orders not supported")
            )
        else:
            return super()._set_chaining_invoice()

    def _get_chaining_invoice_dict(self):
        """Get the chaining invoice dictionary for POS orders"""
        if self.pos_order_ids and len(self.pos_order_ids.ids) == 1:
            pos_order = self.pos_order_ids
            return pos_order._get_chaining_invoice_dict()
        elif len(self.pos_order_ids) > 1:
            # TODO: is possible to have multiple PoS orders for the same Invoice?
            raise exceptions.UserError(
                _("VERI*FACTU: multiple PoS Orders not supported")
            )
        else:
            return super()._get_chaining_invoice_dict()
