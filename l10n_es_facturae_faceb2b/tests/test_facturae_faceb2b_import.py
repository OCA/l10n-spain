# (Copyright) 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

import mock

from odoo.modules.module import get_module_resource

from odoo.addons.component.tests.common import SavepointComponentRegistryCase
from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_certificate import (
    TestL10nEsAeatCertificateBase,
)

try:
    from OpenSSL import crypto
    from zeep import Client
except (ImportError, IOError) as err:
    logging.info(err)

_logger = logging.getLogger(__name__)


class DemoService(object):
    def __init__(self, value):
        self.value = value

    def GetRegisteredInvoices(self, *args):
        return self.value["get_registered"]

    def GetInvoiceCancellations(self, *args):
        return self.value["get_cancelled"]

    def DownloadInvoice(self, *args):
        return self.value["download"]

    def ConfirmInvoiceDownload(self, *args):
        return self.value["confirm"]

    def RejectInvoice(self, *args):
        return self.value["reject"]

    def MarkInvoiceAsPaid(self, *args):
        return self.value["mark_paid"]

    def AcceptInvoiceCancellation(self, *args):
        return self.value["accept_cancellation"]

    def RejectInvoiceCancellation(self, *args):
        return self.value["reject_cancellation"]


class EDIBackendTestCase(TestL10nEsAeatCertificateBase, SavepointComponentRegistryCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls._load_module_components(cls, "component_event")
        cls._load_module_components(cls, "edi")
        cls._load_module_components(cls, "edi_account")
        cls._load_module_components(cls, "l10n_es_facturae")
        cls._load_module_components(cls, "l10n_es_facturae_face")
        cls._load_module_components(cls, "l10n_es_facturae_faceb2b")
        pkcs12 = crypto.PKCS12()
        pkey = crypto.PKey()
        pkey.generate_key(crypto.TYPE_RSA, 512)
        x509 = crypto.X509()
        x509.set_pubkey(pkey)
        x509.set_serial_number(0)
        x509.get_subject().CN = "me"
        x509.set_issuer(x509.get_subject())
        x509.gmtime_adj_notBefore(0)
        x509.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
        x509.sign(pkey, "md5")
        pkcs12.set_privatekey(pkey)
        pkcs12.set_certificate(x509)
        cls.tax = cls.env["account.tax"].create(
            {
                "name": "Test tax",
                "amount_type": "percent",
                "amount": 21,
                "type_tax_use": "sale",
                "facturae_code": "01",
            }
        )

        cls.state = cls.env["res.country.state"].create(
            {
                "name": "Ciudad Real",
                "code": "13",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Cliente de prueba",
                "street": "C/ Ejemplo, 13",
                "zip": "13700",
                "city": "Tomelloso",
                "state_id": cls.state.id,
                "country_id": cls.env.ref("base.es").id,
                "vat": "ES05680675C",
                "facturae": True,
                "attach_invoice_as_annex": False,
                "organo_gestor": "U00000038",
                "unidad_tramitadora": "U00000038",
                "oficina_contable": "U00000038",
                "l10n_es_facturae_sending_code": "faceb2b",
            }
        )
        main_company = cls.env.ref("base.main_company")
        main_company.vat = "ESA12345674"
        main_company.partner_id.country_id = cls.env.ref("base.uk")
        cls.env["res.currency.rate"].search(
            [("currency_id", "=", main_company.currency_id.id)]
        ).write({"company_id": False})
        bank_obj = cls.env["res.partner.bank"]
        cls.bank = bank_obj.search(
            [("acc_number", "=", "FR20 1242 1242 1242 1242 1242 124")], limit=1
        )
        if not cls.bank:
            cls.bank = bank_obj.create(
                {
                    "acc_number": "FR20 1242 1242 1242 1242 1242 124",
                    "partner_id": main_company.partner.id,
                    "bank_id": cls.env["res.bank"]
                    .search([("bic", "=", "PSSTFRPPXXX")], limit=1)
                    .id,
                }
            )
        cls.payment_method = cls.env["account.payment.method"].create(
            {
                "name": "inbound_mandate",
                "code": "inbound_mandate",
                "payment_type": "inbound",
                "bank_account_required": False,
                "active": True,
            }
        )
        payment_methods = cls.env["account.payment.method"].search(
            [("payment_type", "=", "inbound")]
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Test journal",
                "code": "TEST",
                "type": "bank",
                "company_id": main_company.id,
                "bank_account_id": cls.bank.id,
                "inbound_payment_method_ids": [(6, 0, payment_methods.ids)],
            }
        )

        cls.purchase_journal = cls.env["account.journal"].create(
            {
                "name": "Purchase journal",
                "code": "PUR_TEST",
                "type": "purchase",
                "company_id": main_company.id,
                "import_faceb2b": True,
                "facturae_faceb2b_dire": "TEST_DIRE",
            }
        )
        cls.payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "Test payment mode",
                "bank_account_link": "fixed",
                "fixed_journal_id": cls.journal.id,
                "payment_method_id": cls.env.ref(
                    "payment.account_payment_method_electronic_in"
                ).id,
                "show_bank_account_from_journal": True,
                "facturae_code": "01",
            }
        )

        cls.payment_mode_02 = cls.env["account.payment.mode"].create(
            {
                "name": "Test payment mode 02",
                "bank_account_link": "fixed",
                "fixed_journal_id": cls.journal.id,
                "payment_method_id": cls.payment_method.id,
                "show_bank_account_from_journal": True,
                "facturae_code": "02",
            }
        )

        cls.account = cls.env["account.account"].create(
            {
                "company_id": main_company.id,
                "name": "Facturae Product account",
                "code": "facturae_product",
                "user_type_id": cls.env.ref("account.data_account_type_revenue").id,
            }
        )
        cls.invoice_data = open(
            get_module_resource("l10n_es_facturae_faceb2b", "tests", "invoice.xsig"),
            "rb",
        ).read()

    def test_cron_import_ok(self):
        self._activate_certificate(self.certificate_password)
        client = Client(
            wsdl=self.env["ir.config_parameter"].sudo().get_param("facturae.faceb2b.ws")
        )
        integration_code = "TEST_1234"
        responses = {
            "get_registered": client.get_type("ns0:GetRegisteredInvoicesResponseType")(
                client.get_type("ns0:ResultStatusType")(
                    code="0", detail="OK", message="OK"
                ),
                client.get_type("ns0:InvoiceRegistryNumbersType")(
                    registryNumber=[integration_code]
                ),
            ),
            "download": client.get_type("ns0:DownloadInvoiceResponseType")(
                client.get_type("ns0:ResultStatusType")(
                    code="0", detail="OK", message="OK"
                ),
                invoiceFile=client.get_type("ns0:InvoiceFileType")(
                    content=self.invoice_data
                ),
            ),
            "confirm": client.get_type("ns0:ResultStatusType")(
                code="0", detail="OK", message="OK"
            ),
        }
        self.assertFalse(
            self.env["edi.exchange.record"].search(
                [("external_identifier", "=", integration_code)]
            )
        )
        with mock.patch("zeep.client.ServiceProxy") as mock_client:
            mock_client.return_value = DemoService(responses)
            self.env["account.journal"]._cron_facturae_faceb2b()
            exchange_record = self.env["edi.exchange.record"].search(
                [("external_identifier", "=", integration_code)]
            )
            self.assertTrue(exchange_record)
            exchange_record.backend_id.exchange_receive(exchange_record)
            self.assertEqual(exchange_record.edi_exchange_state, "input_received")
            self.assertEqual(exchange_record.record, self.purchase_journal)
            exchange_record.backend_id.exchange_process(exchange_record)
            self.assertEqual(exchange_record.edi_exchange_state, "input_processed")
            self.assertEqual(exchange_record.record._name, "account.move")

    def test_cron_import_error_confirm(self):
        self._activate_certificate(self.certificate_password)
        client = Client(
            wsdl=self.env["ir.config_parameter"].sudo().get_param("facturae.faceb2b.ws")
        )
        integration_code = "TEST_1234"
        responses = {
            "get_registered": client.get_type("ns0:GetRegisteredInvoicesResponseType")(
                client.get_type("ns0:ResultStatusType")(
                    code="0", detail="OK", message="OK"
                ),
                client.get_type("ns0:InvoiceRegistryNumbersType")(
                    registryNumber=[integration_code]
                ),
            ),
            "download": client.get_type("ns0:DownloadInvoiceResponseType")(
                client.get_type("ns0:ResultStatusType")(
                    code="0", detail="OK", message="OK"
                ),
                invoiceFile=client.get_type("ns0:InvoiceFileType")(
                    content=self.invoice_data
                ),
            ),
            "confirm": client.get_type("ns0:ResultStatusType")(
                code="10", detail="OK", message="OK"
            ),
        }
        self.assertFalse(
            self.env["edi.exchange.record"].search(
                [("external_identifier", "=", integration_code)]
            )
        )
        with mock.patch("zeep.client.ServiceProxy") as mock_client:
            mock_client.return_value = DemoService(responses)
            self.env["account.journal"]._cron_facturae_faceb2b()
            exchange_record = self.env["edi.exchange.record"].search(
                [("external_identifier", "=", integration_code)]
            )
            self.assertTrue(exchange_record)
            exchange_record.backend_id.exchange_receive(exchange_record)
            self.assertEqual(exchange_record.edi_exchange_state, "input_received")
            self.assertEqual(exchange_record.record, self.purchase_journal)
            exchange_record.backend_id.exchange_process(exchange_record)
            self.assertEqual(
                exchange_record.edi_exchange_state, "input_processed_error"
            )

    def test_cron_import_no_repeat(self):
        """
        If cron is executed twice, we should not create another exchange record
        """
        self._activate_certificate(self.certificate_password)
        client = Client(
            wsdl=self.env["ir.config_parameter"].sudo().get_param("facturae.faceb2b.ws")
        )
        integration_code = "TEST_1234"
        responses = {
            "get_registered": client.get_type("ns0:GetRegisteredInvoicesResponseType")(
                client.get_type("ns0:ResultStatusType")(
                    code="0", detail="OK", message="OK"
                ),
                client.get_type("ns0:InvoiceRegistryNumbersType")(
                    registryNumber=[integration_code]
                ),
            ),
            "download": client.get_type("ns0:DownloadInvoiceResponseType")(
                client.get_type("ns0:ResultStatusType")(
                    code="0", detail="OK", message="OK"
                ),
                invoiceFile=client.get_type("ns0:InvoiceFileType")(
                    content=self.invoice_data
                ),
            ),
            "confirm": client.get_type("ns0:ResultStatusType")(
                code="10", detail="OK", message="OK"
            ),
        }
        self.assertFalse(
            self.env["edi.exchange.record"].search(
                [("external_identifier", "=", integration_code)]
            )
        )
        with mock.patch("zeep.client.ServiceProxy") as mock_client:
            mock_client.return_value = DemoService(responses)
            self.env["account.journal"]._cron_facturae_faceb2b()
            self.assertEqual(
                1,
                len(
                    self.env["edi.exchange.record"].search(
                        [("external_identifier", "=", integration_code)]
                    )
                ),
            )
            self.env["account.journal"]._cron_facturae_faceb2b()
            self.assertEqual(
                1,
                len(
                    self.env["edi.exchange.record"].search(
                        [("external_identifier", "=", integration_code)]
                    )
                ),
            )

    def test_cron_import_error_download(self):
        self._activate_certificate(self.certificate_password)
        client = Client(
            wsdl=self.env["ir.config_parameter"].sudo().get_param("facturae.faceb2b.ws")
        )
        integration_code = "TEST_1234"
        responses = {
            "get_registered": client.get_type("ns0:GetRegisteredInvoicesResponseType")(
                client.get_type("ns0:ResultStatusType")(
                    code="0", detail="OK", message="OK"
                ),
                client.get_type("ns0:InvoiceRegistryNumbersType")(
                    registryNumber=[integration_code]
                ),
            ),
            "download": client.get_type("ns0:DownloadInvoiceResponseType")(
                client.get_type("ns0:ResultStatusType")(
                    code="10", detail="OK", message="OK"
                ),
            ),
        }
        self.assertFalse(
            self.env["edi.exchange.record"].search(
                [("external_identifier", "=", integration_code)]
            )
        )
        with mock.patch("zeep.client.ServiceProxy") as mock_client:
            mock_client.return_value = DemoService(responses)
            self.env["account.journal"]._cron_facturae_faceb2b()
            exchange_record = self.env["edi.exchange.record"].search(
                [("external_identifier", "=", integration_code)]
            )
            self.assertTrue(exchange_record)
            exchange_record.backend_id.exchange_receive(exchange_record)
            self.assertEqual(exchange_record.edi_exchange_state, "input_receive_error")
            self.assertEqual(exchange_record.record, self.purchase_journal)

    def test_cron_import_no_records(self):
        self._activate_certificate(self.certificate_password)
        client = Client(
            wsdl=self.env["ir.config_parameter"].sudo().get_param("facturae.faceb2b.ws")
        )
        integration_code = "TEST_1234"
        responses = {
            "get_registered": client.get_type("ns0:GetRegisteredInvoicesResponseType")(
                client.get_type("ns0:ResultStatusType")(
                    code="0", detail="OK", message="OK"
                ),
                client.get_type("ns0:InvoiceRegistryNumbersType")(registryNumber=[]),
            ),
        }
        self.assertFalse(
            self.env["edi.exchange.record"].search(
                [("external_identifier", "=", integration_code)]
            )
        )
        with mock.patch("zeep.client.ServiceProxy") as mock_client:
            mock_client.return_value = DemoService(responses)
            self.env["account.journal"]._cron_facturae_faceb2b()
            self.assertFalse(
                self.env["edi.exchange.record"].search(
                    [("external_identifier", "=", integration_code)]
                )
            )

    def test_cron_import_error_get_registered(self):
        self._activate_certificate(self.certificate_password)
        client = Client(
            wsdl=self.env["ir.config_parameter"].sudo().get_param("facturae.faceb2b.ws")
        )
        integration_code = "TEST_1234"
        responses = {
            "get_registered": client.get_type("ns0:GetRegisteredInvoicesResponseType")(
                client.get_type("ns0:ResultStatusType")(
                    code="10", detail="OK", message="OK"
                ),
                client.get_type("ns0:InvoiceRegistryNumbersType")(
                    registryNumber=[integration_code]
                ),
            ),
        }
        self.assertFalse(
            self.env["edi.exchange.record"].search(
                [("external_identifier", "=", integration_code)]
            )
        )
        with mock.patch("zeep.client.ServiceProxy") as mock_client:
            mock_client.return_value = DemoService(responses)
            self.env["account.journal"]._cron_facturae_faceb2b()
            self.assertFalse(
                self.env["edi.exchange.record"].search(
                    [("external_identifier", "=", integration_code)]
                )
            )
