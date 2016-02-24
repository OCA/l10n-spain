# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnológicos <omar@comunitea.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api


class BankingExportSddWizard(models.TransientModel):
    _inherit = 'banking.export.sdd.wizard'

    @api.model
    def generate_group_header_block(self, parent_node, gen_args):
        res = super(BankingExportSddWizard, self).\
            generate_group_header_block(parent_node, gen_args)

        if self.payment_order_ids[0].mode.charge_financed:
            reference = parent_node.xpath('//GrpHdr/MsgId')
            reference[0].text = u"FSDD " + reference[0].text

        return res
