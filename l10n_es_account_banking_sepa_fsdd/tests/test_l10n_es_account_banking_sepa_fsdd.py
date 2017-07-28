# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa S.L. - Luis M. Ontalba
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.addons.account_banking_sepa_direct_debit.tests.test_sdd import \
    TestSDD
from lxml import etree


class TestSDD(TestSDD):

    def test_financed_sdd(self):
        self.payment_mode.charge_financed = True
        super(TestSDD, self).test_sdd()
        action = self.payment_order.open2generated()
        attachment = self.attachment_model.browse(action['res_id'])
        xml_file = attachment.datas.decode('base64')
        xml_root = etree.fromstring(xml_file)
        namespaces = xml_root.nsmap
        namespaces['p'] = xml_root.nsmap[None]
        namespaces.pop(None)
        financed_sepa_xpath = xml_root.xpath('//p:GrpHdr/p:MsgId',
                                             namespaces=namespaces)
        self.assertEquals(financed_sepa_xpath[0].text[0:4], u"FSDD")
