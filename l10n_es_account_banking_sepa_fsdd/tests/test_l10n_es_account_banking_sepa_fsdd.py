# Copyright 2017 Tecnativa - Luis M. Ontalba
# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64

from lxml import etree

from odoo.addons.account_banking_sepa_direct_debit.tests.test_sdd import TestSDDBase


class TestFSDD(TestSDDBase):
    _chart_template_xml_id = "l10n_es.account_chart_template_pymes"

    def test_financed_sdd(self):
        self.payment_mode.charge_financed = True
        invoice = self.create_invoice(self.partner_agrolait.id, self.mandate2, 42.0)
        action = invoice.create_account_payment_line()
        payment_order = self.payment_order_model.browse(action["res_id"])
        payment_order.draft2open()
        action = payment_order.open2generated()
        attachment = self.attachment_model.browse(action["res_id"])
        xml_file = base64.b64decode(attachment.datas)
        xml_root = etree.fromstring(xml_file)
        namespaces = xml_root.nsmap
        namespaces["p"] = xml_root.nsmap[None]
        namespaces.pop(None)
        financed_sepa_xpath = xml_root.xpath(
            "//p:GrpHdr/p:MsgId", namespaces=namespaces
        )
        self.assertEqual(financed_sepa_xpath[0].text[0:4], "FSDD")
