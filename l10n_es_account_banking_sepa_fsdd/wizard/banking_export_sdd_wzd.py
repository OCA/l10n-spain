# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnológicos <omar@comunitea.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import orm, fields


class BankingExportSddWizard(orm.TransientModel):
    _inherit = 'banking.export.sdd.wizard'


    def generate_group_header_block(self, cr, uid, pain_root, gen_args, context=None):
        res = super(BankingExportSddWizard, self).\
            generate_group_header_block(cr, uid, pain_root, gen_args, context=context)
        a=gen_args.get('sepa_export', False)
        if a.payment_order_ids[0].mode.charge_financed:
            reference = pain_root.xpath('//GrpHdr/MsgId')
            reference[0].text = u"FSDD " + reference[0].text

        return res
