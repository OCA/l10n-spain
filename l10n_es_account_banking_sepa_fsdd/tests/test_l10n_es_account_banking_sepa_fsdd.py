# Copyright 2017 Tecnativa - Luis M. Ontalba
# Copyright 2021 Tecnativa - Pedro M. Baeza
# Copyright 2026 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from lxml import etree

from odoo import Command, fields, models
from odoo.tools import file_open

from .common import AccountBankingSepaDirectDebitFSDDCommon


class TestFSDD(AccountBankingSepaDirectDebitFSDDCommon):
    _chart_template_xml_id = "l10n_es.account_chart_template_pymes"

    def _generate_remittance(
        self, payment_mode=None
    ) -> tuple[models.Model, etree._Element]:
        payment_mode = payment_mode or self.payment_mode
        payment_mode.payment_method_id.write(
            {"pain_version": "pain.008.001.02", "mandate_required": True}
        )
        invoice = self.create_invoice(
            self.partner_agrolait.id,
            self.mandate2,
            42.0,
            payment_mode=payment_mode,
        )
        action = invoice.create_account_payment_line()
        payment_order = self.payment_order_model.browse(action["res_id"])
        payment_order.draft2open()
        action = payment_order.open2generated()
        attachment = self.attachment_model.browse(action["res_id"])
        return payment_order, etree.fromstring(bytes(attachment.raw))

    def _message_id(self, xml_root: etree._Element) -> str:
        return xml_root.xpath(
            "string(//*[local-name()='GrpHdr']/*[local-name()='MsgId'])"
        )

    def _assert_valid_sepa_file(
        self, payment_order: models.Model, xml_root: etree._Element
    ) -> None:
        pain_version = payment_order.payment_mode_id.payment_method_id.pain_version
        with file_open(
            f"account_banking_sepa_direct_debit/data/{pain_version}.xsd"
        ) as xsd_file:
            schema = etree.XMLSchema(etree.parse(xsd_file))
        schema.assertValid(xml_root)

    def _assert_remittance_data(
        self, payment_order: models.Model, xml_root: etree._Element
    ) -> None:
        namespaces = {"p": xml_root.nsmap[None]}
        self.assertEqual(
            xml_root.xpath("string(//p:GrpHdr/p:NbOfTxs)", namespaces=namespaces),
            "1",
        )
        self.assertEqual(
            xml_root.xpath("string(//p:GrpHdr/p:CtrlSum)", namespaces=namespaces),
            "42.00",
        )
        self.assertEqual(
            xml_root.xpath(
                "string(//p:DrctDbtTxInf/p:Dbtr/p:Nm)", namespaces=namespaces
            ),
            self.partner_agrolait.name,
        )
        self.assertEqual(
            xml_root.xpath(
                "string(//p:DrctDbtTxInf/p:DbtrAcct/p:Id/p:IBAN)",
                namespaces=namespaces,
            ),
            self.mandate2.partner_bank_id.account_number.replace(" ", ""),
        )
        self.assertEqual(
            xml_root.xpath(
                "string(//p:DrctDbtTxInf/p:DrctDbtTx/p:MndtRltdInf/p:MndtId)",
                namespaces=namespaces,
            ),
            self.mandate2.unique_mandate_reference,
        )
        self.assertEqual(
            xml_root.xpath(
                "string(//p:DrctDbtTxInf/p:DrctDbtTx/p:MndtRltdInf/p:DtOfSgntr)",
                namespaces=namespaces,
            ),
            fields.Date.to_string(self.mandate2.signature_date),
        )
        self.assertEqual(
            xml_root.xpath(
                "string(//p:DrctDbtTxInf/p:InstdAmt)", namespaces=namespaces
            ),
            "42.00",
        )
        self.assertEqual(
            xml_root.xpath(
                "string(//p:DrctDbtTxInf/p:InstdAmt/@Ccy)", namespaces=namespaces
            ),
            "EUR",
        )
        self.assertEqual(
            xml_root.xpath(
                "string(//p:PmtInf/p:CdtrAcct/p:Id/p:IBAN)", namespaces=namespaces
            ),
            self.company_bank.account_number.replace(" ", ""),
        )
        self.assertEqual(
            xml_root.xpath("string(//p:PmtInf/p:ReqdColltnDt)", namespaces=namespaces),
            fields.Date.to_string(payment_order.payment_ids[:1].payment_line_date),
        )

    def test_01_financed_sdd(self) -> None:
        self.payment_mode.charge_financed = True
        payment_order, xml_root = self._generate_remittance()
        message_id = self._message_id(xml_root)
        self.assertTrue(message_id.startswith("FSDD "))
        self.assertEqual(message_id.count("FSDD "), 1)
        self._assert_remittance_data(payment_order, xml_root)
        self._assert_valid_sepa_file(payment_order, xml_root)

        generated_ids = []
        pain_flavor = payment_order.payment_mode_id.payment_method_id.pain_version
        for _ in range(2):
            parent_node = etree.Element("Document")
            payment_order.generate_group_header_block(
                parent_node, {"pain_flavor": pain_flavor}
            )
            generated_ids.append(self._message_id(parent_node))
        self.assertEqual(generated_ids, [message_id, message_id])
        self.assertTrue(all(value.count("FSDD ") == 1 for value in generated_ids))

    def test_02_regular_sdd(self) -> None:
        self.payment_mode.charge_financed = False
        payment_order, xml_root = self._generate_remittance()
        message_id = self._message_id(xml_root)
        self.assertFalse(message_id.startswith("FSDD "))
        self.assertNotIn("FSDD ", message_id)
        self._assert_remittance_data(payment_order, xml_root)
        self._assert_valid_sepa_file(payment_order, xml_root)

    def test_03_payment_mode_settings_are_isolated(self) -> None:
        self.payment_mode.charge_financed = True
        regular_mode = self.env["account.payment.mode"].create(
            {
                "name": "Regular SEPA direct debit",
                "company_id": self.company.id,
                "payment_method_id": self.payment_mode.payment_method_id.id,
                "bank_account_link": "fixed",
                "fixed_journal_id": self.bank_journal.id,
                "sepa_creditor_identifier": False,
            }
        )
        financed_order, financed_xml = self._generate_remittance(self.payment_mode)
        regular_order, regular_xml = self._generate_remittance(regular_mode)
        self.assertTrue(self._message_id(financed_xml).startswith("FSDD "))
        self.assertFalse(self._message_id(regular_xml).startswith("FSDD "))
        self._assert_valid_sepa_file(financed_order, financed_xml)
        self._assert_valid_sepa_file(regular_order, regular_xml)

        other_company_order = self.payment_order_model.with_company(
            self.other_company
        ).create(
            {
                "payment_type": "inbound",
                "payment_mode_id": self.other_company_payment_mode.id,
            }
        )
        other_company_order.payment_mode_id_change()
        parent_node = etree.Element("Document")
        other_company_order.generate_group_header_block(
            parent_node, {"pain_flavor": "pain.008.001.02"}
        )
        other_company_message_id = self._message_id(parent_node)
        self.assertNotIn("FSDD ", other_company_message_id)

    def test_04_supplier_payment_is_not_prefixed(self) -> None:
        payment_method = self.env.ref("account.account_payment_method_manual_out")
        self.bank_journal.outbound_payment_method_line_ids = [
            Command.create(
                {
                    "payment_method_id": payment_method.id,
                    "payment_account_id": self.account_expense_company_B.id,
                }
            )
        ]
        payment_mode = self.env["account.payment.mode"].create(
            {
                "name": "Supplier payments",
                "company_id": self.company.id,
                "bank_account_link": "fixed",
                "fixed_journal_id": self.bank_journal.id,
                "payment_method_id": payment_method.id,
            }
        )
        payment_order = self.payment_order_model.create(
            {"payment_type": "outbound", "payment_mode_id": payment_mode.id}
        )
        payment_order.payment_mode_id_change()
        parent_node = etree.Element("Document")
        payment_order.generate_group_header_block(
            parent_node, {"pain_flavor": "pain.001.001.03"}
        )
        self.assertFalse(self._message_id(parent_node).startswith("FSDD "))
