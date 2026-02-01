# Copyright 2016 Comunitea Servicios Tecnológicos <omar@comunitea.com>
# Copyright 2017 Tecnativa - Luis M. Ontalba <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountPaymentOrder(models.Model):
    _inherit = "account.payment.order"

    def generate_group_header_block(self, parent_node, gen_args):
        res = super().generate_group_header_block(parent_node, gen_args)
        if self.payment_mode_id.charge_financed:
            reference = parent_node.xpath("//GrpHdr/MsgId")
            reference[0].text = "FSDD " + reference[0].text
        return res
